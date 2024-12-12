from dagster import load_assets_from_modules

from . import processing, analytic, visualize
from .processing import TrafficInputConfig

all_assets = load_assets_from_modules(
    modules=[processing, analytic, visualize],
)

__all__ = [
    "all_assets",
    "TrafficInputConfig",
]
