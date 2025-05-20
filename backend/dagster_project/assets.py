import pandas as pd
import os
import json
from typing import List, Optional
from dagster import (
    asset, multi_asset, AssetExecutionContext,
    Output, MetadataValue
)
from dagster import asset_check, AssetCheckResult, AssetCheckSeverity, Config, ConfigurableResource, AssetSpec
import funcutils as fu

from typing import Iterator, List, Tuple
import sqlite3
from itertools import islice

from dagster import asset, Definitions, ResourceDefinition
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from elasticsearch import Elasticsearch, helpers
from resources import SBERT, qdrant, es


class MyAssetConfig(Config):
    filename_texts: str = "/opt/project_data/raw_data.dat.gz"
    filename_prompts_targets: str ="/opt/project_data/sdg_targets.dat"
    filename_prompts_goals: str ="/opt/project_data/sdg_goals.dat"
    current_collection: str = "test"
    batch_size: int=10

@asset
def raw_file_asset(config: MyAssetConfig) :
    file_name = config.filename_texts
    # Load file
    df = fu.load_list(file_name)
    # Attach metadata: number of lines
    metadata = {
        "num_rows": MetadataValue.int(len(df)),
        "file_name": MetadataValue.text(file_name)
    }
    return Output(value=df, metadata=metadata)

@multi_asset(specs=[AssetSpec("targets_asset"), AssetSpec("goals_asset")])
def prompts_asset(config: MyAssetConfig) :
    file_name_targets = config.filename_prompts_targets
    file_name_goals= config.filename_prompts_goals
    # Load file
    df1 = fu.read_dataframe(file_name_targets)
    df2 = fu.read_dataframe(file_name_goals)
    # Attach metadata: number of lines
    metadata1 = {
        "num_rows": MetadataValue.int(len(df1)),
        "file_name": MetadataValue.text(file_name_targets)
    }
    metadata2 = {
        "num_rows": MetadataValue.int(len(df2)),
        "file_name": MetadataValue.text(file_name_goals)
    }
    yield dg.MaterializeResult(value=df1,asset_key="targets_asset", metadata=metadata1)
    yield dg.MaterializeResult(value=df2,asset_key="goals_asset", metadata=metadata2)



@asset_check(asset=raw_file_asset)
def text_column_not_empty(raw_file_asset: pd.DataFrame) -> AssetCheckResult:
    if "text" not in raw_file_asset.columns:
        return AssetCheckResult(passed=False)  
    if raw_file_asset["text"].isnull().any():
        return AssetCheckResult(passed=False)
    return AssetCheckResult(passed=True)


@asset(deps=[raw_file_asset])
def extracted_data_asset(raw_file_asset,config: MyAssetConfig,):
    extracted=fu.process_texts(raw_file_asset.to_dict(orient='records'), fu.keyword1, fu.keyword2)

    stats=fu.analyze_text_data(extracted)
    # Attach metadata: number of lines
    metadata = {
        "stats": MetadataValue.md(json.dumps(stats))
    }

    return Output(value=extracted, metadata=metadata)


@asset(deps=["extracted_data_asset","targets_asset","goals_asset"])
def index_texts(model:SBERT, es_resource: es, qdrant_resource:qdrant,context:AssetExecutionContext,config: MyAssetConfig) -> None:
    """
    Stream a large text file line-by-line, embed each batch with SBERT,
    and upsert into a Qdrant collection.
    """
    batch_size: int = config.batch_size
    model: SentenceTransformer = model.get_transformer
    qdrant_client: QdrantClient = qdrant_resource.get_client
    es_client: ElasticSearch= es_resource.get_client

    # (Re)create collection; adjust name as needed
    es_client.recreate_collection(
        collection_name=config.current_collection,
        vectors_config={
            "size": model.get_sentence_embedding_dimension(),
            "distance": "Cosine",
        },
    )
    texts = extracted_data_asset['text'] 
    ids = extracted_data_asset['text'] 
    embeddings = model.encode(texts, batch_size=batch_size,convert_to_numpy=True)
    points = [
                {
                    "id": int(ids),
                    "vector": embeddings.tolist(),
                    "payload": {"class": ""}
                }
                for doc_id, text, emb in zip(ids, texts, embeddings)
            ]
    es_client.upsert(collection_name=config.current_collection, points=points)

    context.log.info(f"Indexed {len(ids)} texts into Qdrant.")

# 4. Asset: Run threshold search for 17 queries and persist scores
# ------------------
""" @asset(
    config_schema={
        "queries": list,
        "threshold": float,
        "limit": int,
        "output_db_path": str,
    },
    required_resource_keys={"model", "qdrant"},
)
def search_and_store(context) -> str:
    
     Encode a list of queries, run range searches in Qdrant,
     and save (query_id, doc_id, score) triples to SQLite on disk.
    
    queries: List[str] = context.op_config["queries"]
    threshold: float = context.op_config["threshold"]
    limit: int = context.op_config["limit"]
    output_db: str = context.op_config["output_db_path"]

    # Encode queries
    q_embs = model.encode(queries, convert_to_numpy=True)
    for q_idx, q_emb in enumerate(q_embs):
        hits = client.search(
            collection_name="my_texts",
            query_vector=q_emb.tolist(),
            limit=limit,
            score_threshold=threshold,
        )
        rows: List[Tuple[int, int, float]] = [(q_idx, hit.id, hit.score) for hit in hits]
        cur.executemany("INSERT OR IGNORE INTO results VALUES (?, ?, ?)", rows)
        conn.commit()
        context.log.info(f"Query {q_idx}: saved {len(rows)} hits.")

    conn.close()
    return output_db """