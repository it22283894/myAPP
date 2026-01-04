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
            WHERE i.name IN $ingredients
            RETURN d.name AS disease, 
                   sum(r.weight) AS risk_score, 
                   collect(i.name) AS contributing_ingredients
            ORDER BY risk_score DESC
            """
            return session.run(query, ingredients=ingredients).data()
