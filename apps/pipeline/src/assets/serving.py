from geopandas import GeoDataFrame
from dagster import (
    asset,
    AssetIn,
    AssetExecutionContext,
    MetadataValue,
)
from ..sensors import traffic_partitions_def
from ..resources import ClickHouseResource


@asset(
    ins={"gdf": AssetIn("get_congestion_data")},
    partitions_def=traffic_partitions_def,
    kinds={"ClickHouse"},
    description="Save Congestion Data to ClickHouse",
)
def insert_dataframe_clickhouse(
    context: AssetExecutionContext,
    clickhouse: ClickHouseResource,
    gdf: GeoDataFrame,
):
    gdf["geometry"] = gdf["geometry"].apply(
        lambda geom: geom.wkt if geom else None
    )

    client = clickhouse.get_client()
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
    geometry String        -- Geometry as WKT (Well-Known Text) stored as a string
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
