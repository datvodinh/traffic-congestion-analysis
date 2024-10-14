from dagster import asset


@asset(
    kinds={"PowerBI", "SQL"},
    description="Visualize 1",
)
def visualize_table_1(analytic_1):
    pass


@asset(
    kinds={"PowerBI", "SQL"},
    description="Visualize 2",
)
def visualize_table_2(analytic_2, analytic_3):
    pass
