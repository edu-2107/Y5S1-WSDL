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
    query_file = BASE_DIR / "queries" / "actions_for_failure.sparql"

    filter_clause = f"FILTER (?failure = <{failure_uri}>)"

    results = g.run_query_from_file(query_file, filter_clause=filter_clause)

    if not results:
        click.echo(f"No corrective actions defined for failure {failure}.")
        return

    click.echo(f"Recommended actions for {failure}:\n")
    for _, action in results:
        click.echo(f"- {action}")


@app.command("failures")
def failures():
    """
    List all known ErrorContext instances in the graph.
    """
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()

    query = """
    PREFIX onto: <http://example.org/ontomaint#>
    SELECT DISTINCT ?failure ?machine
    WHERE {
      ?failure a onto:ErrorContext .
      OPTIONAL { ?failure onto:affectsMachine ?machine . }
    }
    ORDER BY ?failure
    """

    results = g.run_query(query)

    if not results:
        click.echo("No ErrorContext instances found in the graph.")
        return

    click.echo("Known failures:\n")
    for failure, machine in results:
        if machine:
            click.echo(f"- {failure} (machine: {machine})")
        else:
            click.echo(f"- {failure}")


if __name__ == "__main__":
    app()
