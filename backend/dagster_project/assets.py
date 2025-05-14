import pandas as pd
import gzip
from dagster import (
    asset, AssetExecutionContext,
    Output, MetadataValue
)
from dagster import asset_check, AssetCheckResult, AssetCheckSeverity, Config

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
    file_name: str

@asset
def raw_file_asset(config: MyAssetConfigc) -> Output[pd.DataFrame]:
    file_name = config.file_name
    
    # Load file
    df = load_file(file_name)

    # Attach metadata: number of lines
    metadata = {
        "num_rows": MetadataValue.int(len(df)),
        "file_name": MetadataValue.text(file_name)
    }

    return Output(value=df, metadata=metadata)

@asset_check(asset=raw_file_asset)
def text_column_not_empty(context, raw_file_asset: pd.DataFrame) -> AssetCheckResult:
    if "text" not in raw_file_asset.columns:
        return AssetCheckResult.failed(
            severity=AssetCheckSeverity.ERROR,
            description="Missing 'text' column."
        )
    
    if raw_file_asset["text"].isnull().any():
        return AssetCheckResult.failed(
            severity=AssetCheckSeverity.ERROR,
            description="Some 'text' values are empty."
        )

    return AssetCheckResult.passed()