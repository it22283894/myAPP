import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
from neo4j import GraphDatabase

# --- PAGE CONFIG ---
st.set_page_config(page_title="FoodLens | Health Predictor", layout="wide")

# --- NEO4J CONNECTION ---
class FoodLensDB:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_weighted_risks(self, ingredient_data):
        ingredients = list(ingredient_data.keys())
        # Specify the database name here: foodlensNew
        query = """
        MATCH (i:Ingredient)-[r:AFFECTS]->(d:Disease)
        WHERE i.name IN $names
        RETURN i.name as ingredient, d.name as disease, r.weight as base_weight
        """
        with self.driver.session(database="foodlensnew") as session:
            result = session.run(query, names=ingredients)
            records = result.data()
            
            processed_data = []
            for rec in records:
                grams = ingredient_data.get(rec['ingredient'], 0)
                # Apply the quantitative logic from your proposal
                # Score = (Scientific Weight) * (Dosage/Grams)
                calculated_score = rec['base_weight'] * (grams / 100.0) 
                
                # THRESHOLD: Only keep results with a significant score to avoid "10+ diseases"
                if calculated_score > 0.4: 
                    processed_data.append({
                        "ingredient": rec['ingredient'],
                        "disease": rec['disease'],
                        "score": round(calculated_score, 2)
                    })
            return pd.DataFrame(processed_data)

# --- STYLING ---
st.markdown("""
    <style>
    .stApp { background: #0f172a; color: white; }
    .risk-card {
        background: #8CE4FF; border-left: 8px solid #e63946; padding: 15px;
        border-radius: 10px; margin-bottom: 10px; color: black; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("User Input")
input_raw = st.sidebar.text_area("Ingredients", "sugar, salt")
ingredient_list = [i.strip().lower() for i in input_raw.split(',') if i.strip()]

gram_map = {}
for ing in ingredient_list:
    gram_map[ing] = st.sidebar.number_input(f"Grams of {ing}", min_value=0.0, value=20.0)

analyze_clicked = st.sidebar.button("Analyze Risk")

# --- MAIN ---
st.title("FoodLens: Knowledge Graph Analysis")

if analyze_clicked and ingredient_list:
    # UPDATE THESE WITH YOUR REAL NEO4J CREDENTIALS
    db = FoodLensDB("bolt://localhost:7687", "neo4j", "your_password")
    
    df_results = db.get_weighted_risks(gram_map)

    if not df_results.empty:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("⚠️ Top Health Risks")
            # Group by disease to sum risks from multiple ingredients
            summary = df_results.groupby('disease')['score'].sum().sort_values(ascending=False)
            for disease, total_score in summary.items():
                st.markdown(f'<div class="risk-card">{disease.upper()} <br> Risk Score: {total_score}</div>', unsafe_allow_html=True)

        with col2:
            st.subheader("Knowledge Graph Path")
            nt = Network(height='500px', width='100%', bgcolor="#222222", font_color='white')
            for _, row in df_results.iterrows():
                nt.add_node(row['ingredient'], color='#004e92')
                nt.add_node(row['disease'], color='#e63946')
                nt.add_edge(row['ingredient'], row['disease'], value=row['score'])
            nt.save_graph('graph.html')
            components.html(open('graph.html', 'r').read(), height=520)
    else:
        st.warning("No significant health risks found for these quantities.")
    db.close()
