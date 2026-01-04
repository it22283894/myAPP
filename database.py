from neo4j import GraphDatabase

class FoodLensDB:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(neo4j://127.0.0.1:7687, auth=(neo4j, sakuni200211))

    def close(self):
        self.driver.close()

    def get_risk_paths(self, ingredients):
        with self.driver.session() as session:
            # Cypher query to find diseases linked to multiple ingredients
            query = """
    MATCH (i:Ingredient)-[r:AFFECTS]->(d:Disease)
    WHERE i.name IN $names
    WITH i, d, r
    WHERE r.weight > 0.5  // FILTER: Only show strong scientific evidence
    RETURN i.name as ingredient, d.name as disease, r.weight as base_weight
    """
            return session.run(query, ingredients=ingredients).data()
