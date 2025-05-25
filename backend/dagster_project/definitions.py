from dagster import Definitions, load_assets_from_modules,ResourceDefinition, EnvVar

from sensors import file_update_sensor
import assets
from resources import SBERT, qdrant,es
#from example_job import hello_job
#from my_dagster_project.resources.my_resources import my_resource_defs

all_assets=load_assets_from_modules([assets])

defs = Definitions(
    assets=[
        *all_assets
    ],
    sensors=[
            file_update_sensor],
    # Uncomment and customize if using resources like IO managers
    resources={
        "model": SBERT(),
        "qdrant_resource": qdrant(),
        "es_resource": es( )
    }
)