from dagster import Definitions
from .assets import all_assets

defs = Definitions(
    assets=all_assets,
    # resources=resources_by_deployment_name[deployment_name],
    # sensors=all_sensors,
    # jobs=all_jobs,
)
