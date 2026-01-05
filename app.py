import streamlit as st
import pandas as pd
from neo4j import GraphDatabase
from pyvis.network import Network
import streamlit.components.v1 as components

# --- 1. CONNECTION DETAILS (CRITICAL FIX) ---
# 1. Use 'neo4j+s://' instead of 'https://'
# 2. In Aura Free, the database name is always 'neo4j'
URI = "neo4j+s://629b40da.databases.neo4j.io" 
USER = "neo4j"
PASSWORD = "aqNhn1oXDnvjN2HoCrCDkyIyBJhHhSG6o1naLQ--VT8"
DB_NAME = "neo4j" 

# --- 2. NEO4J CONNECTION CLASS ---
class FoodLensGraph:
    def __init__(self, uri, user, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def get_health_data(self, ingredients):
        # We specify the database name inside the session
        with self.driver.session(database=self.database) as session:
            # Note: This query assumes your nodes have a 'name' property
            query = """
            MATCH (i:Ingredient)-[r]->(d:Disease)
            WHERE toLower(i.name) IN $ing_list
            RETURN i.name AS ingredient, d.name AS disease, r.url AS url
            """
            result = session.run(query, ing_list=[i.lower() for i in ingredients])
            return [record.data() for record in result]

# --- 3. PAGE CONFIG & THEME ---
st.set_page_config(page_title="FoodLens | Health Predictor", page_icon="🥗", layout="wide")

def apply_custom_style():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(15, 23, 42, 0.6), rgba(15, 23, 42, 0.75)), 
                    url('https://images.pexels.com/photos/1565982/pexels-photo-1565982.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2');
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    .risk-card {
        background: #8CE4FF; border-left: 8px solid #e63946;
        padding: 1.2rem; border-radius: 15px; margin-bottom: 12px;
        color: #000000 !important; font-weight: bold;
    }
    h1, h2, h3, h4 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# --- 4. SIDEBAR ---
st.sidebar.header("Input Food Label")
input_raw = st.sidebar.text_area("Enter Ingredients (Comma Separated)", placeholder="e.g., alcohol, sugar")
input_ing = [i.strip().lower() for i in input_raw.split(',') if i.strip()]
analyze_clicked = st.sidebar.button("Analyze & Explain")

# --- 5. MAIN CONTENT ---
st.title("FoodLens: Knowledge Graph Health Predictor 🤓")
st.divider()

if analyze_clicked and input_ing:
    try:
        graph_db = FoodLensGraph(URI, USER, PASSWORD, DB_NAME)
        data = graph_db.get_health_data(input_ing)
        
        if data:
            df_relevant = pd.DataFrame(data)
            col1, col2 = st.columns([1, 1.5])
            
            with col1:
                st.subheader("⚠️ Health Risk Predictions")
                top_diseases = df_relevant['disease'].value_counts().head(5).index
                for d in top_diseases:
                    st.markdown(f'<div class="risk-card">{d.title()}</div>', unsafe_allow_html=True)

            with col2:
                st.subheader("🕸️ Interactive Knowledge Graph")
                nt = Network(height='450px', width='100%', bgcolor="#ffffff", font_color='#101820')
                for _, row in df_relevant.iterrows():
                    nt.add_node(row['ingredient'].title(), color='#004e92', size=25)
                    nt.add_node(row['disease'].title(), color='#e63946', size=20)
                    nt.add_edge(row['ingredient'].title(), row['disease'].title())
                
                nt.save_graph('kg_graph.html')
                components.html(open('kg_graph.html', 'r').read(), height=470)
            
            st.divider()
            st.subheader("📚 Research Sources")
            st.dataframe(df_relevant, use_container_width=True, hide_index=True)
            
        else:
            st.warning("No risks found for these ingredients in the database.")
            
    except Exception as e:
        st.error(f"Failed to connect to Neo4j. Error: {e}")
else:
    st.info("👈 Enter ingredients in the sidebar to begin.")


