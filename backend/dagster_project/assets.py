import pandas as pd
import os
import gzip
import re
import xml.etree.ElementTree as ET
import json
from typing import List, Optional
from dagster import (
    asset, AssetExecutionContext,
    Output, MetadataValue
)
from dagster import asset_check, AssetCheckResult, AssetCheckSeverity, Config
import .utils

nlp = spacy.blank('en')
nlp.add_pipe('sentencizer')

FILE_PATH = "/opt/project_data/raw_data.dat.gz"



class MyAssetConfig(Config):
    file_name: str = FILE_PATH

@asset
def raw_file_asset(config: MyAssetConfig,group_name="ingestion") -> Output[pd.DataFrame]:
    file_name = config.file_name
    # Load file
    df = load_list(file_name)

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


@asset
def extracted_data_asset(config: MyAssetConfig,deps=[raw_file_asset],group_name="sales",context: dg.AssetExecutionContext) -> Output[pd.DataFrame]:
    context.log.info("Extracting data")
    extracted=process_texts(traw_file_asset, keyword1, keyword2)
    stats=analyze_text_data(extracted)

    # Attach metadata: number of lines
    metadata = {
        "num_rows": MetadataValue.int(len(df)),
        "file_name": MetadataValue.text(file_name)
        "stats": dg.MetadataValue.md(json.dumps(stats))
    }
    return Output(value=extracted, metadata=metadata)