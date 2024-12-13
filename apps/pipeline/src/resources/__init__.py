from dagster import EnvVar
from dagster_aws.s3 import S3Resource
from dagster_aws.s3.io_manager import S3PickleIOManager
from .dask import DaskResource
from .clickhouse import ClickHouseResource

aws_access_key_id = EnvVar("AWS_ACCESS_KEY_ID").get_value()
aws_access_key_id = (
    aws_access_key_id.strip() if type(aws_access_key_id) is str else None
)
aws_secret_access_key = EnvVar("AWS_SECRET_ACCESS_KEY").get_value()
aws_secret_access_key = (
    aws_secret_access_key.strip()
    if type(aws_secret_access_key) is str
    else None
)
S3_RESOURCE = S3Resource(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
)

DASK_RESOURCE = {
    "prod": DaskResource(
        address=EnvVar("DASK_URL"),
    ),
    "dev": DaskResource(),
}
CLICKHOUSE_RESOURCE = ClickHouseResource(
    address=EnvVar("CLICKHOUSE_URL"),
    username=EnvVar("CLICKHOUSE_USER"),
    password=EnvVar("CLICKHOUSE_PASSWORD"),
)

RESOURCES_PROD = {
    "s3": S3_RESOURCE,
    "dask": DASK_RESOURCE["prod"],
    "clickhouse": CLICKHOUSE_RESOURCE,
    "io_manager": S3PickleIOManager(
        s3_resource=S3_RESOURCE,
        s3_bucket=EnvVar("S3_BUCKET"),
    ),
}


RESOURCES_DEV = {
    "s3": S3_RESOURCE,
    "dask": DASK_RESOURCE["dev"],
    "clickhouse": CLICKHOUSE_RESOURCE,
}

resources_by_deployment_name = {
    "prod": RESOURCES_PROD,
    "dev": RESOURCES_DEV,
}

__all__ = [
    "resources_by_deployment_name",
]
