import click
from pathlib import Path
from graph_manager import OntoMaintGraph


BASE_DIR = Path(__file__).resolve().parent


def format_uri(uri):
    """Extract local name from URI (e.g., 'http://example.org/ontomaint#Machine' -> 'Machine')"""
    if uri is None:
        return "None"
    uri_str = str(uri)
    if '#' in uri_str:
        return uri_str.split('#')[-1]
    elif '/' in uri_str:
        return uri_str.split('/')[-1]
    return uri_str


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
        click.echo(f"- Affected machine: {format_uri(machine)}")
        click.echo(f"  Blocked job:   {job}")
        if next_job:
            click.echo(f"  Next job:     {next_job}")
        if prop_failure:
            click.echo(f"  May propagate to: {format_uri(prop_failure)}")
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
            click.echo(f"- {failure} (machine: {format_uri(machine)})")
        else:
            click.echo(f"- {failure}")
            

@app.command("whatif")
@click.option("--machine", required=True,
              help="Machine name (e.g. MixerA)")
def whatif(machine):
    """Simulate all failures that affect a given machine."""
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()

    machine_uri = f"http://example.org/ontomaint#{machine}"
    query_file = BASE_DIR / "queries" / "whatif_machine_failure.sparql"

    filter_clause = f"FILTER (?machine = <{machine_uri}>)"

    results = g.run_query_from_file(query_file, filter_clause=filter_clause)

    if not results:
        click.echo(f"No failures affect machine {machine}.")
        return

    click.echo(f"What-if scenario: failures affecting {machine}\n")

    for failure, blockedJob, nextJob in results:
        click.echo(f"- Failure: {format_uri(failure)}")
        click.echo(f"  Blocks job: {format_uri(blockedJob)}")
        if nextJob:
            click.echo(f"  Downstream job: {format_uri(nextJob)}")
        click.echo("")


@app.command("health")
def health():
    """Display overall machine health status."""
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()

    query_file = BASE_DIR / "queries" / "machine_health.sparql"
    results = g.run_query_from_file(query_file)

    if not results:
        click.echo("No machine health data available.")
        return

    click.echo("Machine Health Status:\n")
    click.echo(f"{'Machine':<15} {'Uptime %':<12} {'Failure Rate':<15} {'Age (yrs)':<12} {'Last Maintenance':<20} {'Interval (days)':<15}")
    click.echo("-" * 95)

    for machine, uptime, failure_rate, age, last_maint, interval in results:
        click.echo(f"{format_uri(machine):<15} {str(uptime):<12} {str(failure_rate):<15} {str(age):<12} {str(last_maint):<20} {str(interval):<15}")


@app.command("high-risk")
def high_risk():
    """Identify high-risk failures (near-critical severity)."""
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()

    query_file = BASE_DIR / "queries" / "high_risk_failures.sparql"
    results = g.run_query_from_file(query_file)

    if not results:
        click.echo("No high-risk failures found.")
        return

    click.echo("High-Risk Failures:\n")
    click.echo(f"{'Failure':<20} {'Machine':<15} {'Severity':<10} {'Downtime (min)':<15} {'Cascades':<7} {'Next Failures':<20} {'Action':<20}")
    click.echo("-" * 120)

    for failure, machine, severity, downtime, cascade_count, next_failures, required_action in results:
        click.echo(f"{format_uri(failure):<20} {format_uri(machine):<15} {str(severity):<10} {str(downtime):<15} {str(cascade_count):<7} {format_uri(next_failures):<20} {str(format_uri(required_action)):<20}")


@app.command("maintenance")
def maintenance():
    """Display maintenance schedules for all machines."""
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()

    query_file = BASE_DIR / "queries" / "maintenance_schedule.sparql"
    results = g.run_query_from_file(query_file)

    if not results:
        click.echo("No maintenance schedules found.")
        return

    click.echo("Maintenance Schedules:\n")
    click.echo(f"{'Machine':<15} {'Task':<25} {'Description':<30} {'Due Date':<20} {'Est. Hours':<10} {'Team':<15} {'Specialty':<20}")
    click.echo("-" * 145)

    for machine, task, description, due_date, est_hours, team, specialty in results:
        click.echo(f"{format_uri(machine):<15} {format_uri(task):<25} {str(description):<30} {str(due_date):<20} {str(est_hours):<10} {format_uri(team):<15} {str(specialty):<20}")


@app.command("production")
def production():
    """Analyze production impact of failures."""
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()

    query_file = BASE_DIR / "queries" / "production_impact_analysis.sparql"
    results = g.run_query_from_file(query_file)

    if not results:
        click.echo("No production impact data available.")
        return

    click.echo("Production Impact Analysis:\n")
    click.echo(f"{'Batch':<20} {'Batch Size':<12} {'Date':<20} {'Affected Machines':<18} {'Downtime (min)':<16} {'Severity':<12} {'Cascading':<12}")
    click.echo("-" * 110)

    for batch, batch_size, batch_date, affected_machines, total_downtime, total_severity, cascading in results:
        click.echo(f"{format_uri(batch):<20} {str(batch_size):<12} {str(batch_date):<20} {format_uri(affected_machines):<18} {str(total_downtime):<16} {str(total_severity):<12} {str(cascading):<12}")


@app.command("sensors")
def sensors():
    """Analyze sensor performance and anomalies."""
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()

    query_file = BASE_DIR / "queries" / "sensor_performance.sparql"
    results = g.run_query_from_file(query_file)

    if not results:
        click.echo("No sensor data available.")
        return

    click.echo("Sensor Performance:\n")
    click.echo(f"{'Machine':<20} {'Sensor':<20} {'Metric Name':<20} {'Value':<15} {'Unit':<12} {'Measurement Time':<25}")
    click.echo("-" * 115)

    for machine, sensor, metric_name, metric_value, metric_unit, measurement_time in results:
        click.echo(f"{format_uri(machine):<20} {format_uri(sensor):<20} {str(metric_name):<20} {str(metric_value):<15} {str(metric_unit):<12} {str(measurement_time):<25}")


@app.command("spare-parts")
def spare_parts():
    """Analyze impact of spare parts availability on failures."""
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()

    query_file = BASE_DIR / "queries" / "spare_parts_impact.sparql"
    results = g.run_query_from_file(query_file)

    if not results:
        click.echo("No spare parts data available.")
        return

    click.echo("Spare Parts Impact Analysis:\n")
    click.echo(f"{'Failure':<20} {'Action':<25} {'Part':<20} {'Part Number':<15} {'Lead Time':<12} {'Cost (USD)':<12}")
    click.echo("-" * 105)

    for failure, action, part, part_number, lead_time, cost in results:
        click.echo(f"{format_uri(failure):<20} {format_uri(action):<25} {format_uri(part):<20} {str(part_number):<15} {str(lead_time):<12} {str(cost):<12}")


@app.command("team-workload")
def team_workload():
    """Analyze team workload and maintenance task distribution."""
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()

    query_file = BASE_DIR / "queries" / "team_workload.sparql"
    results = g.run_query_from_file(query_file)

    if not results:
        click.echo("No team workload data available.")
        return

    click.echo("Team Workload Analysis:\n")
    click.echo(f"{'Team':<20} {'Operators':<12} {'Machines Responsible':<20} {'Total Scheduled Hours':<22}")
    click.echo("-" * 75)

    for team, operator_count, machines_responsible, total_hours in results:
        click.echo(f"{format_uri(team):<20} {str(operator_count):<12} {str(machines_responsible):<20} {str(total_hours):<22}")


@app.command("all")
def run_all():
    """Run all analysis queries sequentially."""
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()

    commands = ["health", "critical", "high-risk", "maintenance", "production", "sensors", "spare-parts", "team-workload"]
    
    click.echo("=" * 100)
    click.echo("COMPREHENSIVE SYSTEM ANALYSIS")
    click.echo("=" * 100)
    click.echo()

    for cmd in commands:
        click.echo(f"\n{'='*100}")
        click.echo(f"{cmd.upper()}")
        click.echo(f"{'='*100}\n")
        
        try:
            ctx = click.get_current_context()
            ctx.invoke(globals()[cmd.replace("-", "_")])
        except Exception as e:
            click.echo(f"Error running {cmd}: {e}")


if __name__ == "__main__":
    app()
