from dagster import load_assets_from_modules

from . import processing, serving
from .processing import TrafficInputConfig

all_assets = load_assets_from_modules(
    modules=[processing, serving],
)

__all__ = [
    "all_assets",
    "TrafficInputConfig",
]
