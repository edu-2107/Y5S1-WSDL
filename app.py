import click
from pathlib import Path
from graph_manager import OntoMaintGraph


BASE_DIR = Path(__file__).resolve().parent


@click.group()
def app():
    """OntoMaint app - run maintenance queries and get recommendations."""
    pass


@app.command("init")
def init_graph():
    """Load ontologies + data and run reasoning (dry run)."""
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()


@app.command("impact")
@click.option("--failure", required=True,
              help="URI local name of the ErrorContext (e.g. OverheatingA)")
def impact(failure):
    """
    Diagnose impact of a given failure: machines, jobs, and propagated failures.
    """
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()

    failure_uri = f"http://example.org/ontomaint#{failure}"
    query_file = BASE_DIR / "queries" / "impact_failure.sparql"

    filter_clause = f"FILTER (?failure = <{failure_uri}>)"

    results = g.run_query_from_file(query_file, filter_clause=filter_clause)

    if not results:
        click.echo(f"No impact found for failure {failure}.")
        return

    click.echo(f"Impact for failure {failure}:\n")

    for failure_res, machine, job, next_job, prop_failure in results:
        click.echo(f"- Affected machine: {machine}")
        click.echo(f"  Blocked job:   {job}")
        if next_job:
            click.echo(f"  Next job:     {next_job}")
        if prop_failure:
            click.echo(f"  May propagate to: {prop_failure}")
        click.echo("")
        

@app.command("actions")
@click.option("--failure", required=True,
              help="URI local name of the ErrorContext (e.g. OverheatingA)")
def actions(failure):
    """
    Suggest corrective actions for a failure.
    """
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()

    failure_uri = f"http://example.org/ontomaint#{failure}"

    query = f"""
    PREFIX onto: <http://example.org/ontomaint#>

    SELECT ?action
    WHERE {{
      <{failure_uri}> onto:requiresAction ?action .
    }}
    """

    results = g.run_query(query)
    if not results:
        click.echo("No corrective actions defined for that failure.")
        return

    click.echo(f"Recommended actions for {failure}:")
    for (action,) in results:
        click.echo(f"- {action}")


if __name__ == "__main__":
    app()
