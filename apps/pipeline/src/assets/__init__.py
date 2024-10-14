from dagster import load_assets_from_package_module

from . import processing, analytic, visualize

processing_assets = load_assets_from_package_module(
    package_module=processing,
    group_name="PROCESSING",
)

analytic_assets = load_assets_from_package_module(
    package_module=analytic,
    group_name="ANALYTIC",
)

visualize_assets = load_assets_from_package_module(
    package_module=visualize,
    group_name="VISUALIZE",
)

all_assets = [
    *processing_assets,
    *analytic_assets,
    *visualize_assets,
]
