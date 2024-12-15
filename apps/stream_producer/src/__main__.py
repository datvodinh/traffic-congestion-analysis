import argparse

from src.producer import SimulationConfig, StreamTrafficProducer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream Traffic Producer")

    parser.add_argument(
        "--file",
        "-f",
        type=str,
        required=True,
        help="Path to the csv file",
    )
    parser.add_argument(
        "--speed",
        "-s",
        type=int,
        required=False,
        default=1,
        help="Speed of the simulation (How many seconds in dataset will be streamed in 1 second)",
    )

    args = parser.parse_args()

    producer = StreamTrafficProducer(
        csv_path=args.file,
        config=SimulationConfig(speed=args.speed),
    )
    producer.run()
