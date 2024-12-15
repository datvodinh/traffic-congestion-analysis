import pandas as pd
from dagster import (
    AssetExecutionContext,
    AssetIn,
    MetadataValue,
    asset,
)
from geopandas import GeoDataFrame

from ..resources import ClickHouseResource
from ..sensors import traffic_partitions_def


@asset(
    ins={"gdf": AssetIn("get_congestion_data")},
    partitions_def=traffic_partitions_def,
    kinds={"ClickHouse"},
    description="Save Congestion Data to ClickHouse",
)
def serving_congestion_data(
    context: AssetExecutionContext,
    clickhouse: ClickHouseResource,
    gdf: GeoDataFrame,
):
    gdf["geometry"] = gdf["geometry"].apply(
        lambda ls: [list(coord) for coord in ls.coords]
    )

    client = clickhouse.get_client()
    client.command("DROP TABLE IF EXISTS traffic_data")
    client.command(
        """
    CREATE TABLE IF NOT EXISTS traffic_data (
    segment_id UInt32,         -- Assuming segment IDs are integers
    speed Float32,             -- Speed is a floating-point number
    speed_color String,        -- Speed color is a string (e.g., "Green")
    from_street String,        -- From-street name as a string
    to_street String,          -- To-street name as a string
    street String,             -- Street name as a string
    length Float32,            -- Length as a floating-point number
    hour UInt8,                -- Hour as an 8-bit unsigned integer (0-23)
    geometry LineString            -- Geometry as WKT (Well-Known Text) stored as a string
    ) 
    ENGINE = MergeTree()
    ORDER BY segment_id;""",
    )

    result = client.insert_df(
        table="traffic_data",
        df=gdf,
    )

    context.add_output_metadata(
        {
            "Dataframe": MetadataValue.md(gdf.head().to_markdown()),
            "Total Segment": f"{len(gdf.groupby('segment_id'))} segments",
            "ClickHouse Version": client.server_version,
            "Total Rows Inserted": f"{result.summary['written_rows']} rows",
            "Total Bytes Inserted": f"{result.summary['written_bytes']} bytes",
        },
    )


@asset(
    ins={"agg": AssetIn("aggregation_hour_and_week")},
    partitions_def=traffic_partitions_def,
    kinds={"ClickHouse"},
    description="Save Congestion Data to ClickHouse",
)
def serving_agg_hour_and_week(
    context: AssetExecutionContext,
    clickhouse: ClickHouseResource,
    agg: pd.DataFrame,
):
    client = clickhouse.get_client()
    client.command("DROP TABLE IF EXISTS traffic_data_hour_week")
    client.command(
        """
    CREATE TABLE IF NOT EXISTS traffic_data_hour_week (
        hour UInt8,            -- Hour as an 8-bit unsigned integer (0-23)
        day_of_week UInt8,     -- Week as an 8-bit unsigned integer (0-53)
        bus_count UInt32       -- Bus count as an unsigned 32-bit integer
    )
    ENGINE = MergeTree()
    ORDER BY (hour, day_of_week);
    """
    )

    result = client.insert_df(
        table="traffic_data_hour_week",
        df=agg,
    )

    context.add_output_metadata(
        {
            "Dataframe": MetadataValue.md(agg.head().to_markdown()),
            "ClickHouse Version": client.server_version,
            "Total Rows Inserted": f"{result.summary['written_rows']} rows",
            "Total Bytes Inserted": f"{result.summary['written_bytes']} bytes",
        },
    )


@asset(
    ins={"agg": AssetIn("aggregation_hour_and_month")},
    partitions_def=traffic_partitions_def,
    kinds={"ClickHouse"},
    description="Save Congestion Data to ClickHouse",
)
def serving_agg_hour_and_month(
    context: AssetExecutionContext,
    clickhouse: ClickHouseResource,
    agg: pd.DataFrame,
):
    client = clickhouse.get_client()
    client.command("DROP TABLE IF EXISTS traffic_data_hour_month")
    client.command(
        """
    CREATE TABLE IF NOT EXISTS traffic_data_hour_month (
        hour UInt8,           -- Hour as an 8-bit unsigned integer (0-23)
        month UInt8,          -- Week as an 8-bit unsigned integer (0-12)
        bus_count UInt32      -- Bus count as an unsigned 32-bit integer
    )
    ENGINE = MergeTree()
    ORDER BY (hour, month);
    """
    )

    result = client.insert_df(
        table="traffic_data_hour_month",
        df=agg,
    )

    context.add_output_metadata(
        {
            "Dataframe": MetadataValue.md(agg.head().to_markdown()),
            "ClickHouse Version": client.server_version,
            "Total Rows Inserted": f"{result.summary['written_rows']} rows",
            "Total Bytes Inserted": f"{result.summary['written_bytes']} bytes",
        },
    )
