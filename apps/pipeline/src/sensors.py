import os
from dagster import (
    SkipReason,
    RunRequest,
    sensor,
    SensorEvaluationContext,
    SensorResult,
    DefaultSensorStatus,
    DynamicPartitionsDefinition,
)
from dagster_aws.s3.sensor import get_s3_keys
from dagster_aws.s3 import S3Resource
from typing import List
from .jobs import traffic_partitions_def, traffic_analysis_job


def get_run_requests(
    new_s3_keys: List[str],
) -> List[RunRequest]:
    """Generate RunRequests for the given file type based on the provided batch keys."""
    if len(new_s3_keys) == 0:
        return []

    run_requests = []
    for keys in new_s3_keys:
        run_requests.append(
            RunRequest(
                run_key=None,
                job_name="traffic_analysis_job",
                partition_key=keys,
                run_config={
                    "ops": {
                        "run_processing": {
                            "config": {
                                "keys": keys,
                            }
                        },
                    }
                },
            )
        )
    return run_requests


def create_run_requests_with_keys(
    context: SensorEvaluationContext,
    new_s3_keys: List[str],
    partitions_def: DynamicPartitionsDefinition,
):
    """Create RunRequests for the given file type based on the provided S3 keys."""
    if context.cursor in ["", None]:
        delete_partition_keys = context.instance.get_dynamic_partitions(
            "traffic"
        )
        if len(delete_partition_keys) > 0:
            context.log.info(
                f"These partition will be delete: {delete_partition_keys}"
            )
            return SensorResult(
                run_requests=None,
                cursor=None,
                dynamic_partitions_requests=[
                    partitions_def.build_delete_request(
                        partition_keys=delete_partition_keys,
                    )
                ],
            )
    last_valid_key = new_s3_keys[-1] if new_s3_keys else None
    run_requests = get_run_requests(new_s3_keys=new_s3_keys)

    # Create dynamic partitions requests
    dynamic_partitions_requests = []
    if len(new_s3_keys) > 0:
        dynamic_partitions_requests.append(
            partitions_def.build_add_request(
                partition_keys=new_s3_keys,
            )
        )
    context.log.info(f"Updated cursor to {last_valid_key}")

    return SensorResult(
        run_requests=run_requests,
        cursor=last_valid_key,
        dynamic_partitions_requests=dynamic_partitions_requests,
    )


def get_parquet_prefixs(new_keys: List[str]) -> List[str]:
    """Get the parquet prefix from the new keys."""
    parquet_prefix = []

    for key in new_keys:
        if ".parquet" in key.split("/")[-1]:
            parquet_prefix.append(key.rsplit("/", 1)[0])
    return list(set(parquet_prefix))


@sensor(
    name="traffic_sensor",
    description="Sensor to check for new traffic files in the S3 bucket.",
    default_status=DefaultSensorStatus.STOPPED,
    jobs=[traffic_analysis_job],
)
def check_traffic_data_sensor(
    context: SensorEvaluationContext,
    s3: S3Resource,
) -> SensorResult:
    """A sensor to monitor the specified S3 bucket for new files."""
    # Check for new files in the S3 bucket
    new_s3_keys = get_s3_keys(
        bucket=os.getenv("S3_BUCKET"),
        prefix=os.getenv("TRAFFIC_DATA_PREFIX"),
        since_key=context.cursor or None,
        s3_session=s3.get_client(),
    )
    if not new_s3_keys:
        return SkipReason(
            f"No new s3 files found in the {os.getenv('S3_BUCKET')}\
                {os.getenv('TRAFFIC_DATA_PREFIX')} bucket."
        )

    new_s3_keys = get_parquet_prefixs(new_s3_keys)

    context.log.info(new_s3_keys)

    return create_run_requests_with_keys(
        context=context,
        new_s3_keys=new_s3_keys,
        partitions_def=traffic_partitions_def,
    )


all_sensors = [
    check_traffic_data_sensor,
]
