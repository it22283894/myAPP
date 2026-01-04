import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import os
from neo4j import GraphDatabase

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(
    page_title="FoodLens | Health Effects Finder", 
    page_icon="🥗", 
    layout="wide"
)

def apply_custom_style():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(15, 23, 42, 0.6), rgba(15, 23, 42, 0.85)), 
                    url('https://images.pexels.com/photos/1565982/pexels-photo-1565982.jpeg?cs=srgb&dl=bread-color-copyspace-1565982.jpg&fm=jpg');
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    .stAlert { background-color: rgba(248, 250, 252, 0.9) !important; border-radius: 12px; }
    .stAlert p { color: #000000 !important; font-weight: 600; }
    [data-testid="stSidebar"] { background: rgba(255, 255, 255, 0.6) !important; backdrop-filter: blur(12px); }
    .risk-card {
        background: #8CE4FF; border-left: 8px solid #e63946; padding: 1.2rem;
        border-radius: 15px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        margin-bottom: 12px; color: #000000 !important; font-weight: bold;
        text-transform: uppercase; font-size: 0.85rem;
    }
    h1,h3,h4 { color: white !important; font-weight: 800 !important; }
    h2 { color:#4CCD99 !important ; }
    .stButton>button { width: 100%; border-radius: 15px; background-color: #004e92; color: white; font-weight: bold; }
    [data-testid="stSidebar"] h2 { color: black !important; font-size: 1.5rem !important; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# --- 2. NEO4J CONNECTION CLASS ---
class FoodLensDB:
    def __init__(self, uri, user, password):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        except Exception as e:
            st.error(f"Failed to connect to Neo4j: {e}")

    def close(self):
        self.driver.close()

    def get_weighted_risks(self, ingredient_data):
        """
        Calculates risk scores based on ingredient presence and gram quantity.
        """
        ingredients = list(ingredient_data.keys())
        # Cypher Query: Finds diseases and aggregates weights based on user input
        query = """
        MATCH (i:Ingredient)-[r:AFFECTS]->(d:Disease)
        WHERE i.name IN $names
        RETURN i.name as ingredient, d.name as disease, r.weight as base_weight
        """
        with self.driver.session() as session:
            result = session.run(query, names=ingredients)
            records = result.data()
            
            # Post-processing to factor in grams (The "Quantitative" logic)
            processed_data = []
            for rec in records:
                grams = ingredient_data.get(rec['ingredient'], 0)
                # Logic: Higher grams increase the risk score
                calculated_score = rec['base_weight'] * (grams / 100.0) 
                processed_data.append({
                    "ingredient": rec['ingredient'],
                    "disease": rec['disease'],
                    "score": round(calculated_score, 2)
                })
            return pd.DataFrame(processed_data)

# --- 3. SIDEBAR INPUTS ---
st.sidebar.image("OIP.jpg", width=800)
st.sidebar.header("Input Food Label")
input_raw = st.sidebar.text_area("Enter Ingredients (Comma Separated)", placeholder="sugar, salt, alcohol", height=100)

# Parsing ingredients to create dynamic gram inputs
ingredient_list = [i.strip().lower() for i in input_raw.split(',') if i.strip()]
gram_map = {}

if ingredient_list:
    st.sidebar.markdown("### Specify Quantities (Grams)")
    for ing in ingredient_list:
        gram_map[ing] = st.sidebar.number_input(f"Grams of {ing}", min_value=0.0, value=10.0, step=1.0)

analyze_clicked = st.sidebar.button("Analyze & Explain")

# --- 4. MAIN CONTENT ---
st.markdown("## FoodLens: AI-Powered Health Risk Predictor 🤓")
st.divider()

if analyze_clicked and ingredient_list:
    # Initialize Neo4j (Replace with your actual credentials)
    db = FoodLensDB("bolt://localhost:7687", "neo4j", "password123")
    
    df_results = db.get_weighted_risks(gram_map)

    if not df_results.empty:
        # Filtering logic: Only show risks with high probability (GNN-style threshold)
        top_risks = df_results.groupby('disease')['score'].sum().sort_values(ascending=False)
        top_risks = top_risks[top_risks > 0.5] # Threshold to reduce noise

        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.subheader("⚠️ High Likelihood Risks")
            if top_risks.empty:
                st.write("No high-probability risks found for these quantities.")
            for disease, score in top_risks.items():
                st.markdown(f'<div class="risk-card">{disease} (Score: {score})</div>', unsafe_allow_html=True)
            
            st.info(f"Analyzed {len(ingredient_list)} ingredients. Used quantitative weighting for results.")

        with col2:
            st.subheader("🕸️ Predictive Knowledge Graph")
            nt = Network(height='450px', width='100%', bgcolor="#ffffff", font_color='#101820')
            nt.force_atlas_2based()
            
            for _, row in df_results.iterrows():
                nt.add_node(row['ingredient'].title(), label=row['ingredient'].title(), color='#004e92', size=25)
                nt.add_node(row['disease'].title(), label=row['disease'].title(), color='#e63946', size=20)
                nt.add_edge(row['ingredient'].title(), row['disease'].title(), width=row['score']*5, color='#94a3b8')
            
            nt.save_graph('kg_graph.html')
            components.html(open('kg_graph.html', 'r').read(), height=470)

        st.subheader("🔍 Probability Data Breakdown")
        st.dataframe(df_results, use_container_width=True)
    else:
        st.warning("No health connections found in the Knowledge Graph for these ingredients.")
    
    db.close()
else:
    st.info("👈 Enter ingredients and specify their weights in the sidebar to begin analysis.")
