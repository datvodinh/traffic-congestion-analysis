from dagster import asset
from ...sensors import traffic_partitions_def


@asset(
    partitions_def=traffic_partitions_def,
    kinds={"PowerBI", "SQL"},
    description="Visualize 1",
)
def visualize_table_1(analytic_1):
    pass


@asset(
    partitions_def=traffic_partitions_def,
    kinds={"PowerBI", "SQL"},
    description="Visualize 2",
)
def visualize_table_2(analytic_2, analytic_3):
    pass
