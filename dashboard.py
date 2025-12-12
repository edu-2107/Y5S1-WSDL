import pandas as pd
import streamlit as st
from pathlib import Path
from graph_manager import OntoMaintGraph

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="OntoMaint Dashboard", layout="wide")
st.title("OntoMaint – Semantic Maintenance Dashboard")


# -------------------------
# Helpers
# -------------------------
def local_name(x) -> str:
    s = "" if x is None else str(x)
    return s.split("#")[-1] if "#" in s else s


@st.cache_resource
def load_graph():
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()
    return g


def run_query(query: str):
    g = load_graph()
    return list(g.run_query(query))


# -------------------------
# Top panels: Critical + Sensor alerts
# -------------------------
top_left, top_right = st.columns([1, 1], gap="large")

with top_left:
    st.subheader("Critical failures (severity / downtime)")

    critical_rows = run_query("""
    PREFIX onto: <http://example.org/ontomaint#>
    SELECT ?failure ?machine ?severity ?downtime
    WHERE {
      ?failure a onto:ErrorContext ;
               onto:affectsMachine ?machine ;
               onto:hasSeverity ?severity ;
               onto:hasDowntimeMinutes ?downtime .
    }
    ORDER BY DESC(?severity) DESC(?downtime)
    """)

    if critical_rows:
        df_crit = pd.DataFrame(
            [(local_name(f), local_name(m), int(s), int(d))
             for f, m, s, d in critical_rows],
            columns=["Failure", "Machine", "Severity", "Downtime (min)"]
        )
        st.dataframe(df_crit, use_container_width=True, hide_index=True)
    else:
        st.info("No severity/downtime data found.")


with top_right:
    st.subheader("Sensor alerts")

    alerts_rows = run_query("""
    PREFIX onto: <http://example.org/ontomaint#>
    SELECT ?event ?machine ?temp ?vib ?status ?time
    WHERE {
      ?event a onto:SensorEvent ;
             onto:forMachine ?machine ;
             onto:temperature ?temp ;
             onto:vibration ?vib ;
             onto:status ?status ;
             onto:observedAt ?time .
      FILTER (?status = "ALERT" || ?temp > 80.0 || ?vib > 0.4)
    }
    ORDER BY ?machine ?time
    """)

    if alerts_rows:
        df_alerts = pd.DataFrame(
            [(local_name(e), local_name(m), float(t), float(v), str(sts), str(tm))
             for e, m, t, v, sts, tm in alerts_rows],
            columns=["Event", "Machine", "Temp", "Vibration", "Status", "Time"]
        )
        st.dataframe(df_alerts, use_container_width=True, hide_index=True)
    else:
        st.info("No abnormal sensor events found.")

st.divider()

# -------------------------
# Failure selection + Impact
# -------------------------
failures_rows = run_query("""
PREFIX onto: <http://example.org/ontomaint#>
SELECT DISTINCT ?failure
WHERE {
  ?failure a onto:ErrorContext .
}
ORDER BY ?failure
""")

failure_names = [local_name(f) for (f,) in failures_rows]

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Failure selection")
    selected_name = st.selectbox("Failure", failure_names)
    failure_uri = f"http://example.org/ontomaint#{selected_name}"

with col2:
    st.subheader("Impact")

    impact_rows = run_query(f"""
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
    """)

    df_impact = pd.DataFrame(
        [(local_name(a), local_name(b), local_name(c) if c else "", local_name(d) if d else "")
         for a, b, c, d in impact_rows],
        columns=["Machine", "Blocked job", "Next job", "Propagates to"]
    )
    st.dataframe(df_impact, use_container_width=True, hide_index=True)

st.divider()

# -------------------------
# Recommended actions
# -------------------------
st.subheader("Recommended actions")

actions_rows = run_query(f"""
PREFIX onto: <http://example.org/ontomaint#>
SELECT ?action WHERE {{
  <{failure_uri}> onto:requiresAction ?action .
}}
""")

actions = [local_name(a[0]) for a in actions_rows]
st.write(actions or ["(none)"])

st.divider()

# -------------------------
# SPARQL Query Console
# -------------------------
st.header("SPARQL Query Console")

st.markdown("Explore the knowledge graph using SPARQL queries.")

st.subheader("Query templates")

template = st.selectbox(
    "Choose a template",
    [
        "List all failures",
        "Impact of OverheatingA",
        "Critical failures",
        "What-if: failures affecting FillerB",
        "Sensor alerts"
    ]
)

if template == "List all failures":
    query_text = """PREFIX onto: <http://example.org/ontomaint#>
SELECT ?failure WHERE { ?failure a onto:ErrorContext . }"""

elif template == "Impact of OverheatingA":
    query_text = """PREFIX onto: <http://example.org/ontomaint#>
SELECT ?machine ?job ?nextJob ?propFailure
WHERE {
  onto:OverheatingA onto:affectsMachine ?machine ;
                    onto:blocksJob ?job .
  OPTIONAL { ?job onto:nextJob ?nextJob . }
  OPTIONAL {
    ?fp a onto:FailurePropagation ;
        onto:hasCause onto:OverheatingA ;
        onto:propagatesTo ?propFailure .
  }
}"""

elif template == "Critical failures":
    query_text = """PREFIX onto: <http://example.org/ontomaint#>
SELECT ?failure ?severity ?downtime
WHERE {
  ?failure a onto:ErrorContext ;
           onto:hasSeverity ?severity ;
           onto:hasDowntimeMinutes ?downtime .
}
ORDER BY DESC(?severity)"""

elif template == "What-if: failures affecting FillerB":
    query_text = """PREFIX onto: <http://example.org/ontomaint#>
SELECT ?failure ?job ?nextJob
WHERE {
  ?failure a onto:ErrorContext ;
           onto:affectsMachine onto:FillerB ;
           onto:blocksJob ?job .
  OPTIONAL { ?job onto:nextJob ?nextJob . }
}"""

elif template == "Sensor alerts":
    query_text = """PREFIX onto: <http://example.org/ontomaint#>
SELECT ?machine ?temp ?vib ?status ?time
WHERE {
  ?e a onto:SensorEvent ;
     onto:forMachine ?machine ;
     onto:temperature ?temp ;
     onto:vibration ?vib ;
     onto:status ?status ;
     onto:observedAt ?time .
  FILTER (?status = "ALERT" || ?temp > 80.0 || ?vib > 0.4)
}
ORDER BY ?machine ?time"""

query_text = st.text_area(
    "SPARQL query",
    value=query_text,
    height=250
)

if st.button("Run query"):
    try:
        g = load_graph()
        results = list(g.run_query(query_text))

        if not results:
            st.info("Query executed successfully, but returned no results.")
        else:
            df = pd.DataFrame(
                [[local_name(cell) for cell in row] for row in results]
            )
            st.success(f"Query returned {len(df)} results.")
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error("Error while executing SPARQL query:")
        st.code(str(e))
