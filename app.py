import streamlit as st
from neo4j import GraphDatabase
import pandas as pd

# --- CONNECTION DETAILS ---
# These should ideally go into .streamlit/secrets.toml
URI = "neo4j+s://629b40da.databases.neo4j.io" 
USER = "neo4j"
PASSWORD = "aqNhn1oXDnvjN2HoCrCDkyIyBJhHhSG6o1naLQ--VT8"
DB_NAME = "neo4j" # <--- This specifies your target database

class FoodLensGraph:
    def __init__(self, uri, user, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def get_all_foods(self):
        # We specify the database name inside the session
        with self.driver.session(database=self.database) as session:
            query = "MATCH (f:Food) RETURN f.name AS name, f.calories AS calories, f.protein AS protein"
            result = session.run(query)
            return [record.data() for record in result]

    def add_food(self, name, calories, protein):
        with self.driver.session(database=self.database) as session:
            query = "CREATE (f:Food {name: $name, calories: $calories, protein: $protein})"
            session.run(query, name=name, calories=calories, protein=protein)

# --- STREAMLIT UI ---
st.set_page_config(page_title="FoodLensNew Graph", page_icon="🥝")
st.title("🥝 FoodLensNew: Neo4j Dashboard")

# Initialize the connection
graph_db = FoodLensGraph(URI, USER, PASSWORD, DB_NAME)

tab1, tab2 = st.tabs(["📊 View Library", "➕ Add New Item"])

with tab1:
    st.header(f"Database: {DB_NAME}")
    data = graph_db.get_all_foods()
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No food items found in this graph database yet.")

with tab2:
    st.header("Add to Graph")
    with st.form("add_node"):
        name = st.text_input("Food Name")
        cals = st.number_input("Calories", min_value=0.0)
        prot = st.number_input("Protein (g)", min_value=0.0)
        
        if st.form_submit_button("Create Food Node"):
            if name:
                graph_db.add_food(name, cals, prot)
                st.success(f"Added {name} to {DB_NAME}!")
            else:
                st.error("Please provide a name.")





