import json
import os
import time
import polars as pl
from datetime import datetime
from kafka import KafkaProducer
from dagster import AssetExecutionContext, Config
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class ProducerConfig(Config):
    speed: int = Field(
        default=100,
        description="Speed of the producer",
    )
    topic: str = Field(
        default="traffic",
        description="Kafka topic",
    )
    csv_path: str = Field(
        default="s3://traffic/chicago_stream/sample.csv",
        description="Path to the csv file, from s3",
    )


class StreamTrafficProducer:
    def __init__(
        self,
        config: ProducerConfig,
    ):
        print(os.getenv("KAFKA_URL"))
        self.producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_URL"),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8")
            if k
            else None,  # Serialize key if provided
            security_protocol="SASL_PLAINTEXT",  # Match the broker's protocol
            sasl_mechanism="PLAIN",  # Match the mechanism set in Helm chart
            sasl_plain_username="user1",  # Matches the SASL client user in your Helm chart
            sasl_plain_password="user1_password",
        )
        self.config = config

    def process_data(
        self,
    ) -> list:
        """Read the csv file and group the data by time"""
        df = pl.read_csv(self.config.csv_path)
        rows = df.rows(named=True)

        time_traffic_data = {}

        for row in rows:
            time = row["time"]

            if time not in time_traffic_data:
                time_traffic_data[time] = []

            time_traffic_data[time].append(row)

        return time_traffic_data

    def run(
        self,
        context: AssetExecutionContext,
    ):
        """Send data to Kafka"""
        time_traffic_data = self.process_data()

        for timestamp, data in time_traffic_data.items():
            context.log.info(f"Sending data for timestamp: {timestamp}")
            for row in data:
                self.producer.send(
                    topic=self.config.topic,
                    value=row,
                    key=timestamp,
                )
                context.log.info(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sended for segment_id: {row['segment_id']}"
                )
                time.sleep(1 / self.config.speed)

        context.log.info("Finished")
