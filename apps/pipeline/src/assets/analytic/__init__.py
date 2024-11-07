from dagster import asset


@asset(
    kinds={"Pandas", "Dask"},
    description="Analytic 1",
)
def analytic_1(processed_data):
    pass


@asset(
    kinds={"Pandas", "Dask"},
    description="Analytic 2",
)
def analytic_2(processed_data):
    pass


@asset(
    kinds={"Pandas", "Dask"},
    description="Analytic 3",
)
def analytic_3(processed_data):
    pass
