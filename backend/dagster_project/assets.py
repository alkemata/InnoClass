import pandas as pd
import os
import json
from typing import List, Optional
from dagster import (
    asset, AssetExecutionContext,
    Output, MetadataValue
)
from dagster import asset_check, AssetCheckResult, AssetCheckSeverity, Config
import funcutils as fu

FILE_PATH = "/opt/project_data/raw_data.dat.gz"



class MyAssetConfig(Config):
    file_name: str = FILE_PATH

@asset
def raw_file_asset(config: MyAssetConfig) -> Output[pd.DataFrame]:
    file_name = config.file_name
    # Load file
    df = fu.load_list(file_name)

    # Attach metadata: number of lines
    metadata = {
        "num_rows": MetadataValue.int(len(df)),
        "file_name": MetadataValue.text(file_name)
    }
    dg.MaterializeResult
    return Output(value=df, metadata=metadata)

@asset_check(asset=raw_file_asset)
def text_column_not_empty(context, raw_file_asset: pd.DataFrame) -> AssetCheckResult:
    if "text" not in raw_file_asset.columns:
        return AssetCheckResult(passed=False)  
    if raw_file_asset["text"].isnull().any():
        return AssetCheckResult(passed=False)
    return AssetCheckResult(passed=True)


@asset(deps=[raw_file_asset])
def extracted_data_asset(raw_file_asset,config: MyAssetConfig,) -> Output[pd.DataFrame]:
    
    extracted=fu.process_texts(raw_file_asset["text"], fu.keyword1, fu.keyword2)
    stats=fu.analyze_text_data(extracted)

    # Attach metadata: number of lines
    metadata = {
        "stats": MetadataValue.md(json.dumps(stats))
    }
    return Output(value=extracted, metadata=metadata)