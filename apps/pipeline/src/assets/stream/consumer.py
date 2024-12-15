import json
import os
import geopandas as gpd
from dagster import AssetExecutionContext
from datetime import datetime
from clickhouse_connect.driver.client import Client
from dotenv import load_dotenv
from kafka import KafkaConsumer

load_dotenv()


class StreamTrafficConsumer:
    def __init__(
        self,
        clickhouse_client: Client,
    ):
        self.consumer = KafkaConsumer(
            "traffic",
            bootstrap_servers=f"{os.getenv('KAFKA_HOST')}:{os.getenv('KAFKA_PORT')}",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            auto_offset_reset="earliest",
            group_id="traffic-consumer-group",
        )

        self.clickhouse_client = clickhouse_client

        self.clickhouse_client.command(
            "DROP TABLE IF EXISTS traffic_data_stream"
        )

        query = """
        CREATE TABLE IF NOT EXISTS traffic_data_stream
        (
            segment_id       UInt32,  -- Assuming segment IDs are integers
            speed            Float32, -- Speed is a floating-point number
            congestion_level String,
            from_street      String,  -- From-street name as a string
            to_street        String,  -- To-street name as a string
            street           String,  -- Street name as a string
            length           Float32, -- Length as a floating-point number
            hour             UInt8,   -- Hour as an 8-bit unsigned integer (0-23)
            day_of_week      UInt8,
            month            UInt8,
            start_latitude   Float32,
            start_longitude  Float32,
            end_latitude     Float32,
            end_longitude    Float32,
        )
        ENGINE = MergeTree()
        ORDER BY segment_id;
        """

        self.clickhouse_client.command(query)

    def data_transform(self, data: dict) -> gpd.GeoDataFrame:
        transformed_data = dict((k, [v]) for k, v in data.items())

        df = gpd.GeoDataFrame(transformed_data)

        # Remove rows where speed is -1
        df = df[df["speed"] != -1]

        # New column congestion_level
        df["congestion_level"] = df["speed"].apply(
            lambda x: "Heavy"
            if x > 0 and x < 12
            else "Medium"
            if x >= 12 and x < 18
            else "Low"
        )

        # Keep selected columns
        df = df.loc[
            :,
            [
                "segment_id",
                "speed",
                "congestion_level",
                "from_street",
                "to_street",
                "street",
                "length",
                "hour",
                "day_of_week",
                "month",
                "start_latitude",
                "start_longitude",
                "end_latitude",
                "end_longitude",
            ],
        ]

        return df

    def run(self, context: AssetExecutionContext):
        context.log.info("Starting Kafka Consumer...")
        context.log.info("Current kakfa topics:", list(self.consumer.topics()))

        for message in self.consumer:
            timestamp = message.key
            data = message.value
            context.log.info(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Received: {data} with timestamp: {timestamp}"
            )

            # Process the data
            if data:
                df = self.data_transform(data)

                # Insert the data to ClickHouse
                self.clickhouse_client.insert(
                    table=os.getenv("CLICKHOUSE_TABLE"),
                    data=df,
                )

                context.log.info(f"Inserted {data} to ClickHouse")

            self.consumer.commit()
