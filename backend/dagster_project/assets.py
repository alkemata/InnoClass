import pandas as pd
import os
import json
from typing import List, Optional
from dagster import (
    asset, multi_asset, AssetExecutionContext,
    Output, MetadataValue, MaterializeResult
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
from qdrant_client.models import VectorParams, Distance
import uuid


class MyAssetConfig(Config):
    filename_texts: str = "/opt/project_data/raw_data.dat.gz"
    filename_prompts_targets: str = "/opt/project_data/sdg_targets.dat"
    filename_prompts_goals: str = "/opt/project_data/sdg_goals.dat"
    current_collection: str = "test"
    batch_size: int = 10


@asset
def raw_file_asset(config: MyAssetConfig) -> Output[pd.DataFrame]:
    file_name = config.filename_texts
    # Load file
    try:
        df = fu.load_list(file_name)
    except Exception as e:
        print(f"Error loading File: {e}")
        raise  # Re-raise the exception to fail the asset

    # Attach metadata: number of lines
    metadata = {
        "num_rows": MetadataValue.int(len(df)),
        "file_name": MetadataValue.text(file_name)
    }
    return Output(value=df, metadata=metadata)


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
            result1 = MaterializeResult(asset_key="targets_asset", metadata=metadata1)
        else:
            print(f"targets_asset DataFrame is empty or could not be loaded.")
            result1 = None

        if df2 is not None and not df2.empty:
            metadata2 = {
                "num_rows": MetadataValue.int(len(df2)),
                "file_name": MetadataValue.text(file_name_goals)
            }
            result2 = MaterializeResult(asset_key="goals_asset", metadata=metadata2)
        else:
            print(f"goals_asset DataFrame is empty or could not be loaded.")
            result2 = None

    except Exception as e:
        print(f"Error loading File: {e}")
        raise  # Re-raise to fail the multi-asset

    return result1, result2



@asset_check(asset=raw_file_asset)
def text_column_not_empty(raw_file_asset: pd.DataFrame) -> AssetCheckResult:
    if "text" not in raw_file_asset.columns:
        return AssetCheckResult(passed=False, metadata={"missing_column": "text"})
    if raw_file_asset["text"].isnull().any():
        return AssetCheckResult(passed=False, metadata={"empty_values": raw_file_asset["text"].isnull().sum()})
    return AssetCheckResult(passed=True)



@asset(deps=[raw_file_asset])
def extracted_data_asset(raw_file_asset: pd.DataFrame, config: MyAssetConfig) -> Output[List[dict]]: # Changed return type hint
    extracted = fu.process_texts(raw_file_asset.to_dict(orient='records'), fu.keyword1, fu.keyword2)

    stats = fu.analyze_text_data(extracted)
    # Attach metadata: number of lines
    metadata = {
        "stats": MetadataValue.md(json.dumps(stats))
    }

    return Output(value=extracted, metadata=metadata) # Ensure you return the processed data


@asset(deps=["extracted_data_asset", "targets_asset", "goals_asset"])
def index_texts(context: AssetExecutionContext, model: SBERT, es_resource: es, qdrant_resource: qdrant, config: MyAssetConfig, extracted_data_asset: List[dict]) -> None: # Added extracted_data_asset as argument
    """
    Stream a large text file line-by-line, embed each batch with SBERT,
    and upsert into a Qdrant collection.
    """
    batch_size: int = config.batch_size
    sbert_model: SentenceTransformer = model.get_transformer()
    qdrant_client: QdrantClient = qdrant_resource.get_client()
    es_client: Elasticsearch = es_resource.get_client()

    if not qdrant_client.collection_exists(config.current_collection):
        qdrant_client.create_collection(
            collection_name=config.current_collection,
            vectors_config=VectorParams(size=sbert_model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
        )

    texts = [item['sentence'] for item in extracted_data_asset] # Extract texts
    ids = [item['id'] for item in extracted_data_asset]     # Extract ids
    embeddings = sbert_model.encode(texts, batch_size=batch_size, convert_to_numpy=True)
    points = [
        {
            "id": uuid.uuid4(),
            "vector": emb.tolist(),
            "payload": {"epo_id": str(doc_id), "class": ""}
        }
        for doc_id, text, emb in zip(ids, texts, embeddings)
    ]
    qdrant_client.upsert(collection_name=config.current_collection, points=points)

    context.log.info(f"Indexed {len(ids)} texts into Qdrant.")
