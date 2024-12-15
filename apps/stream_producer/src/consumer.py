import json
import os
from datetime import datetime

import clickhouse_connect
import geopandas as gpd
from clickhouse_connect.driver.client import Client
from dotenv import load_dotenv
from kafka import KafkaConsumer
from pydantic import BaseModel

load_dotenv()


class SimulationConfig(BaseModel):
    speed: int = 1


class ClickHouseResource:
    def __init__(self, address: str, username: str, password: str):
        self.address = address
        self.username = username
        self.password = password

    def get_client(self) -> Client:
        prefix = self.address.split("://")[0]
        host, port = self.address.removeprefix(f"{prefix}://").split(":")
        return clickhouse_connect.get_client(
            host=host,
            port=int(port),
            username=self.username,
            password=self.password,
        )


class StreamTrafficConsumer:
    def __init__(self, config: SimulationConfig = SimulationConfig()):
        self.consumer = KafkaConsumer(
            "traffic",
            bootstrap_servers=f"{os.getenv('KAFKA_HOST')}:{os.getenv('KAFKA_PORT')}",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8") if k else None,
            auto_offset_reset="earliest",
            group_id="traffic-consumer-group",
        )
        self.config = config
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


if __name__ == "__main__":
    consumer = StreamTrafficConsumer()
    consumer.run()
