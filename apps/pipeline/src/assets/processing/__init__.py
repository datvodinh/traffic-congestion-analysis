from dagster import asset
from dagster import Config
from pydantic import Field
from ...sensors import traffic_partitions_def


class TrafficInputConfig(Config):
    keys: str = Field(
        description="S3 keys to process",
    )


@asset(
    partitions_def=traffic_partitions_def,
    kinds={"Python"},
    description="Contain Data ID",
)
def run_processing(config: TrafficInputConfig):
    pass


@asset(
    partitions_def=traffic_partitions_def,
    kinds={"Dask", "Pandas"},
    description="Processing 1",
)
def processing_1(run_processing):
    pass


@asset(
    partitions_def=traffic_partitions_def,
    kinds={"Dask", "Pandas"},
    description="Processing 2",
)
def processing_2(run_processing):
    pass


@asset(
    partitions_def=traffic_partitions_def,
    kinds={"Dask", "Pandas"},
    description="Processing 3",
)
def processed_data(processing_1, processing_2):
    pass
