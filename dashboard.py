import pandas as pd
import streamlit as st
from pathlib import Path
from graph_manager import OntoMaintGraph

BASE_DIR = Path(__file__).resolve().parent
QUERIES_DIR = BASE_DIR / "queries"

st.set_page_config(page_title="OntoMaint Dashboard", layout="wide")
st.title("OntoMaint Dashboard")


# ============================================================
# Per-query parameter metadata
# ============================================================
QUERY_PARAMS = {
    "impact_failure.sparql": {
        "title": "Failure Impact",
        "params": [
            {"var": "?failure", "label": "Failure", "type": "ErrorContext"},
        ],
    },
    "actions_for_failure.sparql": {
        "title": "Corrective Actions",
        "params": [
            {"var": "?failure", "label": "Failure", "type": "ErrorContext", "allow_all": True},
        ],
    },
    "whatif_machine_failure.sparql": {
        "title": "What-if by Machine",
        "params": [
            {"var": "?machine", "label": "Machine", "type": "Machine", "allow_all": True},
        ],
    },
    "critical_failures.sparql": {"title": "Critical Failures", "params": []},
    "high_risk_failures.sparql": {"title": "High-Risk Failures", "params": []},
    "machine_health.sparql": {"title": "Machine Health", "params": []},
    "maintenance_schedule.sparql": {
        "title": "Maintenance Schedule",
        "params": [
            {"var": "?machine", "label": "Machine", "type": "Machine", "allow_all": True},
        ],
    },
}


# ============================================================
# Pretty labels for queries
# ============================================================
def pretty_query_label(filename: str) -> str:
    meta = QUERY_PARAMS.get(filename)
    if meta and meta.get("title"):
        return meta["title"]
    return filename.replace(".sparql", "").replace("_", " ").title()


# ============================================================
# Helpers
# ============================================================
def local_name(x) -> str:
    s = "" if x is None else str(x)
    return s.split("#")[-1] if "#" in s else s


@st.cache_resource
def load_graph():
    g = OntoMaintGraph()
    g.load_ontologies_and_data(BASE_DIR)
    g.apply_reasoning()
    return g


def run_query_raw(query_text: str):
    g = load_graph()
    qr = g.graph.query(query_text)
    vars_ = [str(v) for v in getattr(qr, "vars", [])]
    rows = list(qr)
    return vars_, rows


def rows_to_df(vars_, rows, prettify=True) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    if vars_ and len(vars_) == len(rows[0]):
        cols = [v.lstrip("?") for v in vars_]
    else:
        cols = [f"col{i+1}" for i in range(len(rows[0]))]

    df = pd.DataFrame(
        [[str(cell) if cell is not None else "" for cell in row] for row in rows],
        columns=cols,
    )

    if prettify:
        df = df.applymap(local_name)

    return df


def list_sparql_files() -> list[Path]:
    return sorted(QUERIES_DIR.glob("*.sparql")) if QUERIES_DIR.exists() else []


def load_query_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def inject_filter(query_text: str, filter_snippet: str) -> str:
    if filter_snippet.strip():
        query_text = query_text.replace("# __FILTER__", filter_snippet)
        query_text = query_text.replace("#__FILTER__", filter_snippet)
        query_text = query_text.replace("__FILTER__", filter_snippet)
    else:
        query_text = query_text.replace("# __FILTER__", "")
        query_text = query_text.replace("#__FILTER__", "")
        query_text = query_text.replace("__FILTER__", "")
    return query_text


# ============================================================
# Instance fetchers
# ============================================================
def get_instances_of(class_local_name: str) -> list[str]:
    vars_, rows = run_query_raw(f"""
    PREFIX onto: <http://example.org/ontomaint#>
    SELECT DISTINCT ?x
    WHERE {{ ?x a onto:{class_local_name} . }}
    ORDER BY ?x
    """)
    return [local_name(r[0]) for r in rows] if rows else []


def get_failure_like_instances() -> list[str]:
    vars_, rows = run_query_raw("""
    PREFIX onto: <http://example.org/ontomaint#>
    SELECT DISTINCT ?f
    WHERE {
      { ?f a onto:ErrorContext . }
      UNION { ?f onto:affectsMachine ?m . }
      UNION { ?f onto:blocksJob ?j . }
      UNION {
        ?fp a onto:FailurePropagation ;
            onto:hasCause ?f .
      }
    }
    ORDER BY ?f
    """)
    return [local_name(r[0]) for r in rows] if rows else []


# ============================================================
# Sidebar – Query selection
# ============================================================
st.sidebar.header("Controls")

files = list_sparql_files()
file_names = [f.name for f in files]

query_values = ["__NONE__"] + file_names

selected = st.sidebar.selectbox(
    "Query",
    query_values,
    format_func=lambda v: "— Select a query —" if v == "__NONE__" else pretty_query_label(v),
)

if selected == "__NONE__":
    st.info("Select a query from the sidebar to run it.")
    st.stop()

query_file = QUERIES_DIR / selected
query_name = query_file.name
query_text = load_query_file(query_file)

meta = QUERY_PARAMS.get(query_name, {"title": pretty_query_label(query_name), "params": []})
params = meta["params"]


# ============================================================
# Sidebar – Parameters (with hard-coded batch exclusion)
# ============================================================
st.sidebar.divider()
st.sidebar.subheader("Parameters")

param_values = {}

EXCLUDED_BATCHES = {
    "Batch_2025_12_001",
    "Batch_2025_12_002",
    "Batch_2025_12_003",
}

if not params:
    st.sidebar.caption("This query has no parameters.")
else:
    for p in params:
        p_var = p["var"]
        p_label = p.get("label", p_var)
        p_type = p.get("type")
        allow_all = bool(p.get("allow_all", False))

        if p_type == "Machine":
            options = get_instances_of("Machine")
            options = [m for m in options if m not in EXCLUDED_BATCHES]

        elif p_type == "ErrorContext":
            options = get_failure_like_instances()
        else:
            options = []

        if not options:
            st.sidebar.warning(f"No options found for {p_label}.")
            continue

        if allow_all:
            options = ["All"] + options

        chosen = st.sidebar.selectbox(
            p_label,
            options,
            key=f"{query_name}:{p_var}",
        )

        if chosen != "All":
            param_values[p_var] = chosen


# ============================================================
# Build FILTER
# ============================================================
filter_lines = []
for var, val in param_values.items():
    uri = f"http://example.org/ontomaint#{val}"
    filter_lines.append(f"FILTER ({var} = <{uri}>)")

final_query = inject_filter(query_text, "\n".join(filter_lines))


# ============================================================
# Main – Query Result Viewer
# ============================================================
st.header("Query Result Viewer")
st.caption(f"Query: {pretty_query_label(query_name)}")

c1, c2 = st.columns(2)
show_query = c1.checkbox("Show query text")
prettify = c2.checkbox("Prettify URIs", value=True)

if show_query:
    st.code(final_query, language="sparql")

try:
    vars_, rows = run_query_raw(final_query)
    df = rows_to_df(vars_, rows, prettify)

    if df.empty:
        st.info("Query executed successfully, but returned no results.")
    else:
        st.success(f"Returned {len(df)} rows.")
        st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("Error executing query")
    st.code(str(e))


# ============================================================
# SPARQL Console
# ============================================================
st.divider()
st.header("SPARQL Console")

console_query = st.text_area(
    "Write SPARQL",
    """PREFIX onto: <http://example.org/ontomaint#>
SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 25
""",
    height=180,
)

if st.button("Run console query"):
    try:
        vars_, rows = run_query_raw(console_query)
        df = rows_to_df(vars_, rows, prettify=True)
        if df.empty:
            st.info("No results.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error("Console query error")
        st.code(str(e))
