import os
import base64
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import dask.dataframe as dd
import geopandas as gpd
import dask_geopandas
from shapely.geometry import LineString
from dagster import asset
from io import BytesIO
from dagster import (
    Config,
    AssetExecutionContext,
    MetadataValue,
    AssetIn,
)
from pydantic import Field
from ...resources import DaskResource
from ...sensors import traffic_partitions_def


class TrafficInputConfig(Config):
    keys: str = Field(
        description="S3 keys to process",
    )


def convert_plot_to_metadata(
    plt: plt,
) -> MetadataValue:
    """Convert a matplotlib plot to a base64 encoded image"""
    buffer = BytesIO()
    plt.savefig(buffer)
    data = base64.b64encode(buffer.getvalue())
    return MetadataValue.md(f"![img](data:image/png;base64,{data.decode()})")


@asset(
    partitions_def=traffic_partitions_def,
    kinds={"S3"},
    description="Contain Data ID",
)
def run_config(
    context: AssetExecutionContext,
    config: TrafficInputConfig,
    dask: DaskResource,
):
    try:
        context.log.info(
            f"Reading at {config.keys}",
        )
        endpoint_url = os.getenv("AWS_ENDPOINT_URL")
        with dask.get_client():
            df = dd.read_parquet(
                config.keys,
                storage_options={
                    "anon": True,
                    "endpoint_url": endpoint_url,
                },
            )
            df.columns = df.columns.str.lower()
            total_rows = df.shape[0].compute()

        context.add_output_metadata(
            {
                "Dataframe": MetadataValue.md(df.head().to_markdown()),
                "Total Rows": f"{total_rows} rows",
            },
        )
        return df
    except Exception as e:
        raise e
    # finally:
    #     client.close()


@asset(
    ins={
        "df": AssetIn("run_config"),
    },
    partitions_def=traffic_partitions_def,
    kinds={"Dask"},
    description="Drop Invalid Rows with Negative Speed",
)
def drop_invalid_rows(
    context: AssetExecutionContext,
    dask: DaskResource,
    df: dd.DataFrame,
):
    try:
        with dask.get_client():
            df = df[df["speed"] >= 0]
            total_rows = df.shape[0].compute()
            context.add_output_metadata(
                {
                    "Dataframe": MetadataValue.md(df.head().to_markdown()),
                    "Remaining Rows": f"{total_rows} rows",
                },
            )
        return df
    except Exception as e:
        raise e


@asset(
    ins={
        "df": AssetIn("drop_invalid_rows"),
    },
    partitions_def=traffic_partitions_def,
    kinds={"Dask"},
    description="Get Heatmap Hour and Month by Bus Count",
)
def aggregation_hour_and_month(
    context: AssetExecutionContext,
    dask: DaskResource,
    df: dd.DataFrame,
):
    try:
        with dask.get_client():
            agg = df.groupby(["hour", "month"])["bus_count"].sum().compute()
            pivot = agg.reset_index().pivot(
                index="hour", columns="month", values="bus_count"
            )
            pivot = pivot.fillna(0)

            plt.figure(figsize=(12, 8))
            sns.heatmap(
                pivot,
                annot=False,
                fmt=".0f",
                cmap="coolwarm",
                cbar=True,
                xticklabels=[
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ],
            )
            plt.title("Heatmap of Bus Count by Hour and Month")
            plt.xlabel("Month")
            plt.ylabel("Hour")
            heatmap_hour_month = convert_plot_to_metadata(plt)
            context.add_output_metadata(
                {
                    "Heatmap": heatmap_hour_month,
                }
            )
            return agg.reset_index()
    except Exception as e:
        raise e


@asset(
    ins={
        "df": AssetIn("drop_invalid_rows"),
    },
    partitions_def=traffic_partitions_def,
    kinds={"Dask"},
    description="Get Heatmap Hour and Week by Bus Count",
)
def aggregation_hour_and_week(
    context: AssetExecutionContext,
    dask: DaskResource,
    df: dd.DataFrame,
):
    try:
        with dask.get_client():
            agg = (
                df.groupby(["hour", "day_of_week"])["bus_count"]
                .sum()
                .compute()
            )
            pivot = agg.reset_index().pivot(
                index="hour", columns="day_of_week", values="bus_count"
            )
            pivot = pivot.fillna(0)

            plt.figure(figsize=(12, 8))
            sns.heatmap(
                pivot,
                annot=False,
                fmt=".0f",
                cmap="coolwarm",
                cbar=True,
                xticklabels=[
                    "Sunday",
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                ],
            )
            plt.title("Heatmap of Bus Count by Hour and Day Of Week")
            plt.xlabel("Day of Week")
            plt.ylabel("Hour")
            heatmap_hour_week = convert_plot_to_metadata(plt)
            context.add_output_metadata(
                {
                    "Heatmap": heatmap_hour_week,
                }
            )
            return agg.reset_index()
    except Exception as e:
        raise e


def speed_category(speed):
    """Categorize speed into color"""
    conditions = [
        (speed > 18),
        (speed >= 12) & (speed <= 18),
    ]
    choices = ["Light", "Medium"]
    return np.select(conditions, choices, default="Heavy")


def create_geometry(df):
    """Create geometry column"""
    df["geometry"] = [
        LineString(
            [
                (row["start_longitude"], row["start_latitude"]),
                (row["end_longitude"], row["end_latitude"]),
            ]
        )
        for _, row in df.iterrows()
    ]
    return df


@asset(
    ins={
        "df": AssetIn("drop_invalid_rows"),
    },
    partitions_def=traffic_partitions_def,
    kinds={"Dask"},
    description="Get Congestion Data based on Speed and Hour and return GeoJSON file.",
)
def get_congestion_data(
    context: AssetExecutionContext,
    dask: DaskResource,
    df: dd.DataFrame,
):
    try:
        with dask.get_client():
            agg_method = {
                "speed": "mean",
                "start_latitude": "first",
                "start_longitude": "first",
                "end_latitude": "first",
                "end_longitude": "first",
                "from_street": "first",
                "to_street": "first",
                "street": "first",
                "length": "first",
            }

            context.log.info(f"Aggregating data: {agg_method}")

            result = (
                df.groupby(["segment_id", "hour"])
                .agg(agg_method)
                .reset_index()
                .persist()
            )
            # Map speed to color
            result["congestion_level"] = result["speed"].map_partitions(
                speed_category, meta=("speed", "object")
            )
            # Apply geometry creation
            geometry_meta = {
                col: "float64" for col in result.columns if col != "geometry"
            }
            geometry_meta["geometry"] = "object"
            result = result.map_partitions(
                create_geometry,
                meta=geometry_meta,
            )

            gdf: gpd.GeoDataFrame = dask_geopandas.from_dask_dataframe(result)
            gdf = gdf.compute()

            gdf["speed"].plot.hist(alpha=0.4, bins=100)
            plt.xlabel("Speed (MPH)")
            plt.grid()
            plt.title("Speed Histogram in Chicago")

            speed_histogram = convert_plot_to_metadata(plt)

            gdf.plot(
                column="speed",
                figsize=(10, 10),
                legend=True,
            )
            plt.grid()
            plt.title("Traffic Segments in Chicago")
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")

            chicago_segments = convert_plot_to_metadata(plt)

            context.add_output_metadata(
                {
                    "Dataframe": MetadataValue.md(gdf.head().to_markdown()),
                    "Speed Histogram": speed_histogram,
                    "Chicaco Segments": chicago_segments,
                },
            )
            return gdf

    except Exception as e:
        raise e
