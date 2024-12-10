import os
from dagster import Definitions
from .assets import all_assets
from .jobs import all_jobs
from .sensors import all_sensors
from .resources import resources_by_deployment_name

deployment_name = os.getenv("DAGSTER_DEPLOYMENT", "dev")

defs = Definitions(
    assets=all_assets,
    resources=resources_by_deployment_name[deployment_name],
    sensors=all_sensors,
    jobs=all_jobs,
)
