import pandas as pd
import os
import json
from typing import List, Optional, Tuple
from dagster import (
    asset, multi_asset, AssetExecutionContext,
    Output, MetadataValue, MaterializeResult
)
from dagster import asset_check, AssetCheckResult, AssetCheckSeverity, Config, ConfigurableResource, AssetSpec
import funcutils as fu

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from elasticsearch import Elasticsearch, helpers
# from resources import SBERT, qdrant, es # Removed direct import, will access via context
from qdrant_client.models import VectorParams, Distance
import uuid


class MyAssetConfig(Config):
    filename_texts: str = "/opt/project_data/raw_data.dat.gz"
    filename_prompts_targets: str = "/opt/project_data/sdg_targets.dat"
    filename_prompts_goals: str = "/opt/project_data/sdg_goals.dat"
    current_collection: str = "test"
    batch_size: int = 10
    search_results_file: str = "/opt/project_data/search_results.csv" # Added output file path
    threshold: float =0.6



@asset
def raw_file_asset(config: MyAssetConfig):
    file_name = config.filename_texts
    # Load file
    try:
        metadata,data = fu.load_list(file_name)
    except Exception as e:
        print(f"Error loading File: {e}")
        raise  # Re-raise the exception to fail the asset

    # Attach metadata: number of lines
    metadata = {
        "num_rows": MetadataValue.int(len(data)),
        "file_name": MetadataValue.text(file_name),
        "preview": MetadataValue.md(metadata["extract_method"])
    }
    return Output(value=data, metadata=metadata)


@multi_asset(specs=[AssetSpec("targets_asset"), AssetSpec("goals_asset")])
def prompts_asset(config: MyAssetConfig) -> Tuple[Optional[MaterializeResult], Optional[MaterializeResult]]:
    file_name_targets = config.filename_prompts_targets
    file_name_goals = config.filename_prompts_goals

    df1: Optional[pd.DataFrame] = None  # Initialize to None
    df2: Optional[pd.DataFrame] = None  # Initialize to None
    result1: Optional[MaterializeResult] = None
    result2: Optional[MaterializeResult] = None

    try:
        df1 = fu.read_dataframe(file_name_targets)
        df2 = fu.read_dataframe(file_name_goals)

        # Attach metadata: number of lines
        # Check if df1 and df2 are not None before trying to use them
        if df1 is not None and not df1.empty:
            metadata1 = {
                "num_rows": MetadataValue.int(len(df1)),
                "file_name": MetadataValue.text(file_name_targets)
            }
            df1.pickle("./storage/goals_asset")
            result1 = MaterializeResult(asset_key="targets_asset", metadata=metadata1)
        else:
            print(f"targets_asset DataFrame is empty or could not be loaded.")
            result1 = None

        if df2 is not None and not df2.empty:
            metadata2 = {
                "num_rows": MetadataValue.int(len(df2)),
                "file_name": MetadataValue.text(file_name_goals)
            }
            df2.pickle("./storage/goals_asset")
            result2 = MaterializeResult(asset_key="goals_asset", metadata=metadata2)
        else:
            print(f"goals_asset DataFrame is empty or could not be loaded.")
            result2 = None

    except Exception as e:
        print(f"Error loading File: {e}")
        raise  # Re-raise to fail the multi-asset

    return result1, result2


@asset_check(asset=raw_file_asset)
def text_column_not_empty(raw_file_asset: list[dict]) -> AssetCheckResult:
    # Convert list of dictionaries to DataFrame for easier processing,
    # especially for `isnull().any()` and `isnull().sum()`
    df = pd.DataFrame(raw_file_asset)

    if "text" not in df.columns:
        return AssetCheckResult(passed=False, metadata={"missing_column": "text"})

    if df["text"].isnull().any():
        return AssetCheckResult(passed=False, metadata={"empty_values": df["text"].isnull().sum()})

    return AssetCheckResult(passed=True)


@asset(deps=[raw_file_asset])
def extracted_data_asset(raw_file_asset, config: MyAssetConfig) -> Output[List[dict]]:  # Changed return type hint
    extracted = fu.process_texts(raw_file_asset, fu.keyword1, fu.keyword2)

    stats = fu.analyze_text_data(extracted)
    # Attach metadata: number of lines
    metadata = {
        "stats": MetadataValue.md(json.dumps(stats))
    }

    return Output(value=extracted, metadata=metadata)  # Ensure you return the processed data


@asset(deps=["extracted_data_asset"])
def index_texts(context: AssetExecutionContext, config: MyAssetConfig, extracted_data_asset: List[dict]) -> None:  # Added extracted_data_asset
    """
    Stream a large text file line-by-line, embed each batch with SBERT,
    and upsert into a Qdrant collection.
    """
    batch_size: int = config.batch_size
    sbert_model: SentenceTransformer = context.resources.model.get_transformer() # Get resources from context
    qdrant_client: QdrantClient = context.resources.qdrant.get_client()
    es_client: Elasticsearch = context.resources.es.get_client()

    if not qdrant_client.collection_exists(config.current_collection):
        qdrant_client.create_collection(
            collection_name=config.current_collection,
            vectors_config=VectorParams(size=sbert_model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
        )

    texts = [item['sentence'] for item in extracted_data_asset]  # Extract texts
    ids = [item['id'] for item in extracted_asset]  # Extract ids
    embeddings = sbert_model.encode(texts, batch_size=batch_size, convert_to_numpy=True)
    points = [
        models.PointStruct(id=str(docs_id), vector=emb.tolist(), payload={"epo_id": str(docs_id), "class": ""})
        for idi, text, emb, docs_id in zip(range(1, len(ids) + 1), texts, embeddings, ids) # Corrected the range
    ]
    qdrant_client.upsert(collection_name=config.current_collection, points=points)

    context.log.info(f"Indexed {len(ids)} texts into Qdrant.")





# 4. Asset: Run threshold search for 17 queries and persist scores
# ------------------
@asset(
    deps=["index_texts", "targets_asset", "goals_asset"],)
def search_and_store(context: AssetExecutionContext, config: MyAssetConfig, goals_asset: pd.DataFrame) -> str:
    """
    Encode a list of queries, run range searches in Qdrant,
    and save scores to a CSV file.
    """
    queries = goals_asset.tolist()
    threshold: float = config.threshold
    limit: int = config.limit
    output_file_path: str = config.search_results_file # Get output file from config

    sbert_model: SentenceTransformer = context.resources.model.get_transformer() # Get resources from context
    qdrant_client: QdrantClient = context.resources.qdrant.get_client()

    # Encode queries
    q_embs = sbert_model.encode(queries, convert_to_numpy=True)
    results = [] # List to store results before saving
    for q_idx, q_emb in enumerate(q_embs):
        hits = qdrant_client.search(
            collection_name=config.current_collection,
            query_vector=q_emb.tolist(),
            score_threshold=threshold,
        )
        for hit in hits:
            results.append({
                "query_index": q_idx,
                "hit_id": hit.id,
                "score": hit.score,
                "epo_id": hit.payload.get("epo_id"), # Extract epo_id from payload
            })

    # Convert results to DataFrame and save to CSV
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_file_path, index=False) # save the results
    context.log.info(f"Search results saved to {output_file_path}")
    return output_file_path # Return file path

@asset(deps=[raw_file_asset])
def es_patent_light(context: AssetExecutionContext,raw_file_asset, config: MyAssetConfig):

    es_client: Elasticsearch = context.resources.es.get_client()
    INDEX_NAME=config.current_collection
    if es_client.indices.exists(index=INDEX_NAME):
        context.log.info(f"Deleting existing index: {INDEX_NAME}")
        es_client.indices.delete(index=INDEX_NAME, ignore=[400, 404])

    index_mapping = {
        "properties": {
            "original_text": { # For keyword search (BM25)
                "type": "text",
                "analyzer": "standard" # Use a suitable analyzer
            },
            "idepo": {type:"text"},
            "pubnbr": {type:"keyword"},
            "title":    { # For keyword search (BM25)
                "type": "text",
                "analyzer": "standard" # Use a suitable analyzer
            },
            "sdg": {"type": "keyword"},
            "target": {"type": "keyword"}
            # Add other fields from your JSON if you want to index/search them
        }
    }

    context.log.info(f"Creating index: {INDEX_NAME} with mapping...")
    try:
        es_client.indices.create(
            index=config.current_collection,
            body=index_mapping,
        )
    except Exception as e:
        print(f"Error creating index: {e}")
        exit()
    docs_to_index = []
    for text in raw_file_asset:
        doc = {
            "_index": INDEX_NAME,
            "idepo": text["id"],
            "pubnbr": text["pubnbr"],
            "original_text": text["original_text"],
            "title": text["title"],
            "sdg":[""],
            "target":[""]
            }
        docs_to_index.append(doc)

    context.log.info(f"Bulk indexing {len(docs_to_index)} documents...")
    try:
        helpers.bulk(es_client, docs_to_index)
    except Exception as e:
        context.log.info(f"Error during bulk indexing: {e}")
        raise