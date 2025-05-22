import os
from dagster import sensor, SensorEvaluationContext, RunRequest, SkipReason, AssetSelection,Field
from assets import raw_file_asset

class FileUpdateSensorConfig(Config):
    file_path: str="/opt/project_data/test.dat.gz"

@sensor(
    asset_selection=AssetSelection.assets(raw_file_asset)
)
def file_update_sensor(context: SensorEvaluationContext, config: FileUpdateSensorConfig):
    file_name = "/opt/project_data/raw_data.dat.gz"

    if not os.path.exists(file_name):
        return SkipReason(f"File does not exist: {file_name}")

    mtime = os.path.getmtime(file_name)
    last_mtime = float(context.cursor or "0")

    if mtime > last_mtime:
        context.update_cursor(str(mtime))
        return RunRequest()
    
    return SkipReason("No changes detected.")