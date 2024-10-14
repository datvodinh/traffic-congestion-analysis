from dagster import asset


@asset(
    kinds={"Python"},
    description="Contain Data ID",
)
def run_processing():
    pass


@asset(
    kinds={"Dask", "Pandas"},
    description="Processing 1",
)
def processing_1(run_processing):
    pass


@asset(
    kinds={"Dask", "Pandas"},
    description="Processing 2",
)
def processing_2(run_processing):
    pass


@asset(
    kinds={"Dask", "Pandas"},
    description="Processing 3",
)
def processed_data(processing_1, processing_2):
    pass
