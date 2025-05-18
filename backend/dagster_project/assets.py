import pandas as pd
import os
import json
from typing import List, Optional
from dagster import (
    asset, multi-asset AssetExecutionContext,
    Output, MetadataValue
)
from dagster import asset_check, AssetCheckResult, AssetCheckSeverity, Config, ConfigurableResource
import funcutils as fu

from typing import Iterator, List, Tuple
import sqlite3
from itertools import islice

from dagster import asset, Definitions, ResourceDefinition
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient


class MyAssetConfig(Config):
    filename_texts: str = "/opt/project_data/raw_data.dat.gz"
    filename_prompts_targets: str ="/opt/project_data/sdg_targets.dat"
    filename_prompts_goals: str ="/opt/project_data/sdg_goals.dat"

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

@multi_asset(specs=[dg.AssetSpec("targets_asset"), dg.AssetSpec("goals_asset")])
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
        "file_name": MetadataValue.text(file_name_goalss)
    }
    yield dg.MaterializeResult(value=d1,asset_key="targets_asset", metadata=metadata1)
    yield dg.MaterializeResult(value=d2,asset_key="goals_asset", metadata=metadata2)



@asset_check(asset=raw_file_asset)
def text_column_not_empty(context, raw_file_asset: pd.DataFrame) -> AssetCheckResult:
    if "text" not in raw_file_asset.columns:
        return AssetCheckResult(passed=False)  
    if raw_file_asset["text"].isnull().any():
        return AssetCheckResult(passed=False)
    return AssetCheckResult(passed=True)


@asset(deps=[raw_file_asset])
def extracted_data_asset(raw_file_asset,config: MyAssetConfig,):
    extracted=fu.process_texts(raw_file_asset.to_dict(orient='records'), fu.keyword1, fu.keyword2)
    stats=fu.analyze_text_data(extracted)
    print(stats)
    # Attach metadata: number of lines
    metadata = {
        "stats": MetadataValue.md(json.dumps(stats))
    }
    return Output(value=extracted, metadata=metadata)

 

@asset(deps=extracted_data_asset,required_resource_keys={"SBERT", "qdrant"}
)
def index_texts(context) -> None:
    """
    Stream a large text file line-by-line, embed each batch with SBERT,
    and upsert into a Qdrant collection.
    """
    file_path: str = context.op_config["file_path"]
    batch_size: int = context.op_config["batch_size"]
    model: SentenceTransformer = SBERT
    client: QdrantClient = qdrant

    # (Re)create collection; adjust name as needed
    client.recreate_collection(
        collection_name="my_texts",
        vectors_config={
            "size": model.get_sentence_embedding_dimension(),
            "distance": "Cosine",
        },
    )

    # Stream, embed, upsert
    with open(file_path, encoding="utf8") as f:
        id_counter = 0
        for batch in batcher((line.rstrip("\n") for line in f), batch_size):
            embeddings = model.encode(batch, convert_to_numpy=True)
            points = []
            for text, emb in zip(batch, embeddings):
                points.append({"id": id_counter, "vector": emb.tolist(), "payload": {"text": text}})
                id_counter += 1
            client.upsert(collection_name="my_texts", points=points)

    context.log.info(f"Indexed {id_counter} texts into Qdrant.")
