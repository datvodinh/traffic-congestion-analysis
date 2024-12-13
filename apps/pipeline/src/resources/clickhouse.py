import clickhouse_connect
from clickhouse_connect.driver.client import Client
from dagster import ConfigurableResource


class ClickHouseResource(ConfigurableResource):
    address: str
    username: str
    password: str

    def get_client(self) -> Client:
        prefix = self.address.split("://")[0]
        host, port = self.address.removeprefix(f"{prefix}://").split(":")
        return clickhouse_connect.get_client(
            host=host,
            port=int(port),
            username=self.username,
            password=self.password,
        )
