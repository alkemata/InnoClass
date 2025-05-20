from dagster import Definitions, load_assets_from_modules

from sensors import file_update_sensor
from assets import text_column_not_empty
from resources import SBERT_resource, qdrant_client_resource,es
#from example_job import hello_job
#from my_dagster_project.resources.my_resources import my_resource_defs
import dagster_project as assets

all_assets=oad_assets_from_modules([assets])

defs = Definitions(
    assets=[
        *all_assets
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