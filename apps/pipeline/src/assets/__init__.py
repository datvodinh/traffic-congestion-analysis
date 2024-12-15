from dagster import load_assets_from_package_module
from . import batch, stream

batch_assets = load_assets_from_package_module(
    package_module=batch,
    group_name="BATCH",
)

stream_assets = load_assets_from_package_module(
    package_module=stream,
    group_name="STREAM",
)

all_assets = batch_assets + stream_assets

__all__ = [
    "all_assets",
]
