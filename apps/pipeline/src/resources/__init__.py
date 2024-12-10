import os
from dagster import EnvVar
from dagster_aws.s3 import S3Resource
from dagster_aws.s3.io_manager import S3PickleIOManager
from .dask import DaskResource


S3_RESOURCE = S3Resource(
    aws_access_key_id=EnvVar("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=EnvVar("AWS_SECRET_ACCESS_KEY"),
)

DASK_RESOURCE = DaskResource(
    address=os.getenv("DASK_URL", None),
)

RESOURCES_PROD = {
    "s3": S3_RESOURCE,
    "dask": DASK_RESOURCE,
    "io_manager": S3PickleIOManager(
        s3_resource=S3_RESOURCE,
        s3_bucket=EnvVar("S3_BUCKET"),
    ),
}


RESOURCES_DEV = {
    "s3": S3_RESOURCE,
    "dask": DASK_RESOURCE,
}

resources_by_deployment_name = {
    "prod": RESOURCES_PROD,
    "dev": RESOURCES_DEV,
}

__all__ = [
    "resources_by_deployment_name",
]
