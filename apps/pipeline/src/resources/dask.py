from dagster import ConfigurableResource
from dask.distributed import Client, LocalCluster
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class DaskResource(ConfigurableResource):
    address: Optional[str] = None

    def get_client(self) -> Client:
        if self.address:
            return Client(self.address)
        else:
            return Client(LocalCluster())
