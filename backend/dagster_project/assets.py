import pandas as pd
import os
import json
from typing import List, Optional
from dagster import (
    asset, AssetExecutionContext,
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

FILE_PATH = "/opt/project_data/raw_data.dat.gz"



class MyAssetConfig(Config):
    file_name: str = FILE_PATH

@asset
def raw_file_asset(config: MyAssetConfig) :
    file_name = config.file_name
    # Load file
    df = fu.load_list(file_name)
    # Attach metadata: number of lines
    metadata = {
        "num_rows": MetadataValue.int(len(df)),
        "file_name": MetadataValue.text(file_name)
    }
    return Output(value=df, metadata=metadata)

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

class SBERT(ConfigurableResource):
    model: str = "all-MiniLM-L6-v2"

    def get_transformer():
        return SentenceTransformer(model)

# Qdrant client resource
def qdrant_client_resource(_init_context) -> QdrantClient:
    return QdrantClient(url="http://qdrant:6333", prefer_grpc=True)    

@asset(required_resource_keys={"SBERT", "qdrant"}
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
