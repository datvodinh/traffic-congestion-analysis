import os
from dagster import (
    DynamicPartitionsDefinition,
    define_asset_job,
    multiprocess_executor,
    ExecutorDefinition,
)
from dagster_k8s import k8s_job_executor

traffic_partitions_def = DynamicPartitionsDefinition(name="traffic")

check_k8s_job_executor: bool = os.getenv("DAGSTER_DEPLOYMENT", "dev") != "dev"
executor_def: ExecutorDefinition = (
    k8s_job_executor if check_k8s_job_executor else multiprocess_executor
)


traffic_analysis_job = define_asset_job(
    description="Process and analyze traffic data from Chicago city.",
    name="traffic_analysis_job",
    selection="run_config*",
    partitions_def=traffic_partitions_def,
    tags={"asset": "traffic"},
)

all_jobs = [traffic_analysis_job]
