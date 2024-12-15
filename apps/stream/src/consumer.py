import json
import os
from datetime import datetime

import clickhouse_connect
import geopandas as gpd
from clickhouse_connect.driver.client import Client
from dotenv import load_dotenv
from kafka import KafkaConsumer

load_dotenv()


class ClickHouseResource:
    def __init__(self, address: str, username: str, password: str):
        self.address = address
        self.username = username
        self.password = password

    def init_table(self, client: Client):
        query = f"""
        CREATE TABLE IF NOT EXISTS {os.getenv("CLICKHOUSE_TABLE")}
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

        client.command(query)

    def get_client(self) -> Client:
        prefix = self.address.split("://")[0]
        host, port = self.address.removeprefix(f"{prefix}://").split(":")
        client = clickhouse_connect.get_client(
            host=host,
            port=int(port),
            username=self.username,
            password=self.password,
        )

        # Init the table
        self.init_table(client)

        return client


class StreamTrafficConsumer:
    def __init__(self):
        self.consumer = KafkaConsumer(
            "traffic",
            bootstrap_servers=f"{os.getenv('KAFKA_HOST')}:{os.getenv('KAFKA_PORT')}",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            auto_offset_reset="earliest",
            group_id="traffic-consumer-group",
        )
        self.clickhouse_client = ClickHouseResource(
            address=f"http://{os.getenv('CLICKHOUSE_HOST')}:{os.getenv('CLICKHOUSE_PORT')}",
            username="",
            password="",
        ).get_client()

    def reset_connection(self):
        self.clickhouse_client = ClickHouseResource(
            address=f"http://{os.getenv('CLICKHOUSE_HOST')}:{os.getenv('CLICKHOUSE_PORT')}",
            username="",
            password="",
        ).get_client()

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

    def run(self):
        print("Starting Kafka Consumer...")
        print("Current kakfa topics:", list(self.consumer.topics()))

        for message in self.consumer:
            timestamp = message.key
            data = message.value
            print(
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

                print(f"Inserted {data} to ClickHouse")

            self.consumer.commit()


if __name__ == "__main__":
    # Check all the environment variables are set
    print("Checking environment variables...")

    for env_var in [
        "KAFKA_HOST",
        "KAFKA_PORT",
        "CLICKHOUSE_HOST",
        "CLICKHOUSE_PORT",
        "CLICKHOUSE_TABLE",
    ]:
        print(f"Checking {env_var}...")
        print(f"In the environment: {os.getenv(env_var)}")

    consumer = StreamTrafficConsumer()
    consumer.run()
