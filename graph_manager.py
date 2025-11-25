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

        for ttl in ont_dir.glob("*.ttl"):
            print(f"Loading ontology: {ttl}")
            self.graph.parse(ttl, format="turtle")

        for ttl in data_dir.glob("*.ttl"):
            print(f"Loading data: {ttl}")
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
        """
        Run a SPARQL query over the graph.
        """
        return list(self.graph.query(query_str))
