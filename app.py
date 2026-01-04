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
# --- 2. DATABASE CLASS ---
class FoodLensDB:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # ADD THE FUNCTION RIGHT HERE
    def get_weighted_risks(self, ingredient_data):
        ingredients = list(ingredient_data.keys())
        
        # We add 'ORDER BY base_weight DESC' to get the most important ones first
        query = """
        MATCH (i:Ingredient)-[r:AFFECTS]->(d:Disease)
        WHERE i.name IN $names
        RETURN i.name as ingredient, d.name as disease, r.weight as base_weight
        ORDER BY r.weight DESC
        """
        
        with self.driver.session(database="foodlensnew") as session:
            result = session.run(query, names=ingredients)
            records = result.data()
            
            processed_data = []
            for rec in records:
                # Use the grams from your sidebar input
                grams = ingredient_data.get(rec['ingredient'], 0)
                
                # Logic: Score = Scientific Weight * (Grams / 100)
                # This ensures small amounts don't trigger "Disease Predictions"
                calculated_score = rec['base_weight'] * (grams / 100.0) 
                
                # ONLY ADD TO LIST IF THE SCORE IS HIGH (Fixes the "10+ disease" issue)
                if calculated_score > 0.5: 
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
    
    df_results

