from pathlib import Path
from rdflib import Graph
from owlrl import DeductiveClosure, OWLRL_Semantics


class OntoMaintGraph:
    def __init__(self):
        self.graph = Graph()

    def load_ontologies_and_data(self, base_dir: Path):
        """
        Load all .ttl files from ontologies/ and data/ into the graph.
        """
        ont_dir = base_dir / "ontologies"
        data_dir = base_dir / "data"

        #print(f"Ontology dir: {ont_dir} exists={ont_dir.exists()}")
        #print(f"Data dir:     {data_dir} exists={data_dir.exists()}")

        for ttl in ont_dir.glob("*.ttl"):
            #print(f"Loading ontology: {ttl}")
            self.graph.parse(ttl, format="turtle")

        for ttl in data_dir.glob("*.ttl"):
            #print(f"Loading data: {ttl}")
            self.graph.parse(ttl, format="turtle")

        print(f"Graph loaded with {len(self.graph)} triples.")

    def apply_reasoning(self):
        """
        Apply OWL RL reasoning to materialize inferred triples.
        """
        print("Running OWL RL reasoning...")
        DeductiveClosure(OWLRL_Semantics).expand(self.graph)
        print(f"After reasoning: {len(self.graph)} triples.")

    def run_query(self, query_str: str):
        return list(self.graph.query(query_str))

    def run_query_from_file(self, query_file: Path, filter_clause: str = ""):
        text = query_file.read_text(encoding="utf-8")
        text = text.replace("__FILTER__", filter_clause)
        print("Running query from:", query_file)
        return self.run_query(text)
