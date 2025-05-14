import pandas as pd
import os
import gzip
import re
import xml.etree.ElementTree as ET
import spacy
import json
from typing import List, Optional
from dagster import (
    asset, AssetExecutionContext,
    Output, MetadataValue
)
from dagster import asset_check, AssetCheckResult, AssetCheckSeverity, Config

nlp = spacy.blank('en')
nlp.add_pipe('sentencizer')

FILE_PATH = "/opt/project_data/raw_data.dat.gz"

def load_list(filename):
    """
    Loads a gzipped JSON Lines (jsonl) file and returns a list of dictionaries.

    Parameters:
        filename (str): The filename of the gzipped jsonl file.

    Returns:
        list: A list of dictionaries read from the file.
    """
    result = []
    with gzip.open(filename, 'rt', encoding='utf-8') as f:
        for line in f:
            result.append(json.loads(line))
    return pd.DataFrame(result)

class MyAssetConfig(Config):
    file_name: str = FILE_PATH

@asset
def raw_file_asset(config: MyAssetConfig) -> Output[pd.DataFrame]:
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

# Keywords to search for in headings (allowing fuzzy matching with up to one error)
keyword1 = ["scope of the invention","Description of the Related Art", "TECHNICAL SCOPE","Description of Related Art","REVEALING THE INVENTION","background of the invention", "background of the disclosure", "field of the invention", "technical field","summary","industrial applicability","field of the disclosure","background",  "prior art", "state of the art"]
keyword2=["background","The present invention regards","herein described subject matter", "It is well known" "technology described herein", "field of the disclosure", "field of the invention", "subject of the invention", "belongs to the field", "invention is","invention relates to", "present invention refers to"]


@asset
def extracted_data_asset(config: MyAssetConfig) -> Output[pd.DataFrame]:
    file_name = config.file_name
    
    # Load file
    df = load_list(file_name)

    # Attach metadata: number of lines
    metadata = {
        "num_rows": MetadataValue.int(len(df)),
        "file_name": MetadataValue.text(file_name)
    }