from dagster import Definitions
from assets import raw_file_asset,extracted_data_asset, prompts_asset
from sensors import file_update_sensor
from assets import text_column_not_empty
from resources import SBERT_resource, qdrant_client_resource,es
#from example_job import hello_job
#from my_dagster_project.resources.my_resources import my_resource_defs


defs = Definitions(
    assets=[
        raw_file_asset,prompts_asset,extracted_data_asset,index_texts, search_and_store,
    ],
    asset_checks=[
        text_column_not_empty,  # optional
    ],
    sensors=[
        file_update_sensor,
    ],
    # Uncomment and customize if using resources like IO managers
    resources={
        "SBERT": ResourceDefinition.hardcoded_resource(SBERT),
        "qdrant": ResourceDefinition.hardcoded_resource(qdrant),
        "es": ResourceDefinition.hardcoded_resource(es)
    }
)