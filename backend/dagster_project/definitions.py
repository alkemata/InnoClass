from dagster import Definitions
#from my_dagster_project.assets import my_asset_group1, my_asset_group2
from example_job import hello_job
#from my_dagster_project.resources.my_resources import my_resource_defs

defs = Definitions(
    jobs=[hello_job]
)