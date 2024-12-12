import base64
import seaborn as sns
import matplotlib.pyplot as plt
import dask.dataframe as dd
from dagster import asset
from io import BytesIO
from dagster import (
    Config,
    AssetExecutionContext,
    MetadataValue,
    AssetIn,
)
from pydantic import Field
from ..resources import DaskResource
from ..sensors import traffic_partitions_def


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
    kinds={"Python"},
    description="Contain Data ID",
)
def run_config(
    context: AssetExecutionContext,
    config: TrafficInputConfig,
):
    context.log.info(
        f"Reading at {config.keys}",
    )

    df = dd.read_parquet(config.keys)
    df.columns = df.columns.str.lower()
    total_rows = df.shape[0].compute()

    context.add_output_metadata(
        {
            "Dataframe": MetadataValue.md(df.head().to_markdown()),
            "Total Rows": f"{total_rows} rows",
        },
    )

    return df


@asset(
    ins={
        "df": AssetIn("run_config"),
    },
    partitions_def=traffic_partitions_def,
    kinds={"Dask", "Pandas"},
    description="Processing 1",
)
def get_heatmap_hour_and_month(
    context: AssetExecutionContext,
    dask: DaskResource,
    df: dd.DataFrame,
):
    client = dask.get_client()
    try:
        df = df[df["speed"] >= 0]

        agg = df.groupby(["hour", "month"])["bus_count"].sum().compute()

        # step 3: create a pivot table
        pivot = agg.reset_index().pivot(
            index="hour", columns="month", values="bus_count"
        )

        # fill nan values for visualization
        pivot = pivot.fillna(0)

        # step 4: plot heatmap
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
    except Exception as e:
        raise e
    finally:
        client.close()


@asset(
    ins={
        "df": AssetIn("run_config"),
    },
    partitions_def=traffic_partitions_def,
    kinds={"Dask", "Pandas"},
    description="Processing 1",
)
def get_heatmap_hour_and_week(
    context: AssetExecutionContext,
    dask: DaskResource,
    df: dd.DataFrame,
):
    client = dask.get_client()
    try:
        df = df[df["speed"] >= 0]

        agg = df.groupby(["hour", "day_of_week"])["bus_count"].sum().compute()

        # create a pivot table
        pivot = agg.reset_index().pivot(
            index="hour", columns="day_of_week", values="bus_count"
        )

        # fill nan values for visualization
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
    except Exception as e:
        raise e
    finally:
        client.close()


@asset(
    partitions_def=traffic_partitions_def,
    kinds={"Dask", "Pandas"},
    description="Processing 3",
)
def processed_data(get_heatmap_hour_and_month, get_heatmap_hour_and_week):
    pass
