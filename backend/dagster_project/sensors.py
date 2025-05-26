from dagster import (
    sensor, SensorEvaluationContext, RunRequest, SkipReason,
    define_asset_job, AssetSelection, DefaultSensorStatus
)
# Assuming your assets are in 'assets.py' in the same directory/package
from assets import training_set_creation # Adjust if your project structure is different
# from datetime import datetime # Not strictly needed if ES timestamps are ISO strings
from elasticsearch import Elasticsearch # For type hinting

# 1. Define the job that the sensor will trigger
training_set_update_job = define_asset_job(
    name="training_set_update_job",
    selection=AssetSelection.assets(training_set_creation)
)

# Default index name, can be made configurable if needed
ES_INDEX_NAME = "main_table" 

@sensor(
    job=training_set_update_job,
    minimum_interval_seconds=60, # Check every 60 seconds
    default_status=DefaultSensorStatus.RUNNING, # Make sensor active by default
    required_resource_keys={"es_resource"},
)
def elasticsearch_update_sensor(context: SensorEvaluationContext):
    # Type hint for es_client, though it's provided by the resource
    es_client: Elasticsearch = context.resources.es_resource.get_client()
    
    # Initialize cursor to a very old timestamp string for the first run
    # Elasticsearch date format for {{_ingest.timestamp}} is typically ISO 8601
    last_cursor_iso = context.cursor if context.cursor else "1970-01-01T00:00:00.000Z"
    
    context.log.info(f"Sensor checking for updates in '{ES_INDEX_NAME}' since cursor: {last_cursor_iso}")

    try:
        query = {
            "query": {
                "bool": {
                    "filter": [
                        {"range": {"last_updated": {"gt": last_cursor_iso}}}
                    ]
                }
            },
            # Sort by 'last_updated' descending to get the newest document first.
            # "format" helps ES correctly interpret the timestamp string.
            "sort": [{"last_updated": {"order": "desc", "format": "strict_date_optional_time_nanos"}}],
            "size": 10,  # We only need a few to get the latest timestamp and confirm changes.
                         # If many docs are updated simultaneously, this ensures we get the true latest for the cursor.
            "_source": ["last_updated"] # Only need the last_updated field from source.
        }
        
        response = es_client.search(index=ES_INDEX_NAME, body=query)
        hits = response.get("hits", {}).get("hits", [])

        if hits:
            # The first hit is the most recent one due to descending sort
            most_recent_update_ts = hits[0]["_source"]["last_updated"]
            
            # Log the number of new/updated documents found based on the query size
            # For total count, you might inspect response['hits']['total']['value']
            # but for cursor purposes, the timestamp of the latest document is key.
            num_new_or_updated_in_batch = len(hits) 
            context.log.info(
                f"Found {num_new_or_updated_in_batch} new/updated documents (out of potentially more) "
                f"in '{ES_INDEX_NAME}' since last check. Most recent update: {most_recent_update_ts}."
            )
            
            # Update cursor to the timestamp of the most recent document found in this batch
            context.update_cursor(most_recent_update_ts)
            
            return RunRequest(
                run_key=f"es_update_{most_recent_update_ts}", # Unique run key using the latest timestamp
                # run_config can be added here if the job/asset needs specific config, e.g.,
                # run_config={"ops": {"my_op": {"config": {"param": "value"}}}}
            )
        else:
            context.log.info(f"No new updates found in '{ES_INDEX_NAME}' since {last_cursor_iso}.")
            return SkipReason(f"No new document updates detected in '{ES_INDEX_NAME}' since {last_cursor_iso}.")

    except Exception as e:
        # Log the error and skip this tick to avoid breaking the sensor
        # Use context.log.exception for full traceback if preferred
        context.log.error(f"Error during Elasticsearch sensor execution: {e}")
        return SkipReason(f"Error querying Elasticsearch for sensor: {e}")

        my_job = define_asset_job("my_job", selection=[raw_file_asset])

@sensor(minimum_interval_seconds=5,
    default_status=DefaultSensorStatus.RUNNING,)
def file_update_sensor(context: SensorEvaluationContext):
    file_name = "/opt/project_data/raw_data.dat.gz"

    if not os.path.exists(file_name):
        return SkipReason(f"File does not exist: {file_name}")

    mtime = os.path.getmtime(file_name)
    last_mtime = float(context.cursor or "0")

    if mtime > last_mtime:
        context.update_cursor(str(mtime))
        return RunRequest(job_name="my_job")
    
    return SkipReason("No changes detected.")
