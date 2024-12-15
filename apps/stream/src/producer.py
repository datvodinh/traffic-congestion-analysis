import json
import os
import time
from datetime import datetime

import polars as pl
from dotenv import load_dotenv
from kafka import KafkaProducer
from pydantic import BaseModel

load_dotenv()


class SimulationConfig(BaseModel):
    speed: int = 1


class StreamTrafficProducer:
    def __init__(self, csv_path: str, config: SimulationConfig = SimulationConfig()):
        self.producer = KafkaProducer(
            bootstrap_servers=f"{os.getenv('KAFKA_HOST')}:{os.getenv('KAFKA_PORT')}",
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8")
            if k
            else None,  # Serialize key if provided
        )
        self.csv_path = csv_path
        self.config = config

    def process_data(self) -> list:
        """
        Read the csv file and group the data by time
        """
        df = pl.read_csv(self.csv_path)
        rows = df.rows(named=True)

        time_traffic_data = {}

        for row in rows:
            time = row["time"]

            if time not in time_traffic_data:
                time_traffic_data[time] = []

            time_traffic_data[time].append(row)

        return time_traffic_data

    def run(self):
        time_traffic_data = self.process_data()

        for timestamp, data in time_traffic_data.items():
            print(f"Sending data for timestamp: {timestamp}")
            for row in data:
                self.producer.send(
                    topic="traffic",
                    value=row,
                    key=timestamp,
                )
                print(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sended for segment_id: {row['segment_id']}"
                )

            time.sleep(1 / self.config.speed)

        print("Finished")
