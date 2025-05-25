import os
from dagster import sensor, SensorEvaluationContext, RunRequest, SkipReason, AssetSelection,Field,Config,define_asset_job
from assets import raw_file_asset

my_job = define_asset_job("my_job", selection=[raw_file_asset])

@sensor(job="my_job",minimum_interval_seconds=5,
    default_status=dg.DefaultSensorStatus.RUNNING)

def file_update_sensor(context: SensorEvaluationContext):
    file_name = "/opt/project_data/raw_data.dat.gz"

    if not os.path.exists(file_name):
        return SkipReason(f"File does not exist: {file_name}")

    mtime = os.path.getmtime(file_name)
    last_mtime = float(context.cursor or "0")

    if mtime > last_mtime:
        context.update_cursor(str(mtime))
        return RunRequest()
    
    return SkipReason("No changes detected.")