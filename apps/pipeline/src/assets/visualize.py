import base64
import matplotlib.pyplot as plt
from io import BytesIO
from geopandas import GeoDataFrame
from dagster import (
    asset,
    AssetIn,
    AssetExecutionContext,
    MetadataValue,
)
from ..sensors import traffic_partitions_def
from ..resources import ClickHouseResource


def convert_plot_to_metadata(
    plt: plt,
) -> MetadataValue:
    """Convert a matplotlib plot to a base64 encoded image"""
    buffer = BytesIO()
    plt.savefig(buffer)
    data = base64.b64encode(buffer.getvalue())
    return MetadataValue.md(f"![img](data:image/png;base64,{data.decode()})")


@asset(
    ins={"gdf": AssetIn("get_congestion_data")},
    partitions_def=traffic_partitions_def,
    kinds={"ClickHouse"},
    description="Save Congestion Data to ClickHouse",
)
def visualize_congestion_tableau(
    context: AssetExecutionContext,
    clickhouse: ClickHouseResource,
    gdf: GeoDataFrame,
):
    # client = clickhouse.get_client()
    context.add_output_metadata(
        {
            "Dataframe": MetadataValue.md(gdf.head().to_markdown()),
            "Total Segment": f"{len(gdf.groupby('segment_id'))} segments",
            # "ClickHouse Version": client.server_version,
        },
    )
