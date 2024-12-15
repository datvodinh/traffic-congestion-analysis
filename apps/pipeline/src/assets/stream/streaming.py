from dagster import asset, AssetExecutionContext
from .producer import ProducerConfig, StreamTrafficProducer
from .consumer import StreamTrafficConsumer
from ...resources import ClickHouseResource


@asset(
    description="Kafka Producer",
    kinds={"KafKa"},
)
def kafka_producer(
    context: AssetExecutionContext,
    config: ProducerConfig,
):
    producer = StreamTrafficProducer(
        config=config,
    )

    producer.run(context=context)


@asset(
    description="Kafka Consumer",
    kinds={"KafKa"},
)
def kafka_consumer(
    context: AssetExecutionContext,
    clickhouse: ClickHouseResource,
):
    client = clickhouse.get_client()
    consumer = StreamTrafficConsumer(client)
    consumer.run(context=context)
