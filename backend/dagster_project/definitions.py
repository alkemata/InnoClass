from dagster import Definitions, load_assets_from_modules,ResourceDefinition, EnvVar

from .sensors import file_update_sensor, my_job, elasticsearch_update_sensor, training_set_update_job # Updated imports
import assets
from .resources import SBERT, qdrant, es # Using relative import for consistency
#from example_job import hello_job
#from my_dagster_project.resources.my_resources import my_resource_defs

all_assets=load_assets_from_modules([assets])

defs = Definitions(
    assets=[
        *all_assets # training_set_creation will be included here by load_assets_from_modules
    ],
    jobs=[my_job, training_set_update_job], # Added training_set_update_job
    sensors=[
            file_update_sensor,
            elasticsearch_update_sensor # Added elasticsearch_update_sensor
            ],
    # Uncomment and customize if using resources like IO managers
    resources={
        "model": SBERT(),
        "qdrant_resource": qdrant(),
        "es_resource": es( )
    }
)