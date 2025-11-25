import click
from pathlib import Path
from .graph_manager import OntoMaintGraph


BASE_DIR = Path(__file__).resolve().parent.parent


@click.group()
def cli():
    """OntoMaint CLI - run maintenance queries and get recommendations."""
    pass


@cli.command("init")
def init_graph():
    """Load ontologies + data and run reasoning (dry run)."""
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()


@cli.command("impact")
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

    query = f"""
    PREFIX onto: <http://example.org/ontomaint#>

    SELECT ?machine ?job ?nextJob ?propFailure
    WHERE {{
      <{failure_uri}> a onto:ErrorContext ;
                       onto:affectsMachine ?machine ;
                       onto:blocksJob ?job .

      OPTIONAL {{ ?job onto:nextJob ?nextJob . }}

      OPTIONAL {{
        ?fp a onto:FailurePropagation ;
            onto:hasCause <{failure_uri}> ;
            onto:propagatesTo ?propFailure .
      }}
    }}
    """

    results = g.run_query(query)
    if not results:
        click.echo("No impact found for that failure.")
        return

    for row in results:
        machine, job, next_job, prop_failure = row
        click.echo(f"- Machine: {machine}")
        click.echo(f"  Blocks job: {job}")
        if next_job:
            click.echo(f"  Downstream job: {next_job}")
        if prop_failure:
            click.echo(f"  May propagate to: {prop_failure}")
        click.echo("")
        

@cli.command("actions")
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
    cli()
