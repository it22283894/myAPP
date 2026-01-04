import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
from neo4j import GraphDatabase

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(page_title="FoodLens | Health Predictor", layout="wide")

# --- 2. DATABASE CLASS ---
class FoodLensDB:
    def __init__(self, uri, user, password):
        # Using a context manager for the driver is safer
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_weighted_risks(self, ingredient_data):
        ingredients = list(ingredient_data.keys())
        # The Cypher query looks for connections in your specific DB
        query = """
        MATCH (i:Ingredient)-[r:AFFECTS]->(d:Disease)
        WHERE i.name IN $names
        RETURN i.name as ingredient, d.name as disease, r.weight as base_weight
        """
        # We specify your database name "foodlensNew" here
        with self.driver.session(database="foodlensNew") as session:
            result = session.run(query, names=ingredients)
            records = result.data()
            
            processed_data = []
            for rec in records:
                grams = ingredient_data.get(rec['ingredient'], 0)
                # Apply your research logic: Score based on quantity
                calculated_score = rec['base_weight'] * (grams / 100.0) 
                
                # Threshold to filter out the "10+ diseases" problem
                if calculated_score > 0.4: 
                    processed_data.append({
                        "ingredient": rec['ingredient'],
                        "disease": rec['disease'],
                        "score": round(calculated_score, 2)
                    })
            return pd.DataFrame(processed_data)

# --- 3. SIDEBAR ---
st.sidebar.header("Input Food Label")
input_raw = st.sidebar.text_area("Enter Ingredients (comma separated)", "sugar, salt")
ingredient_list = [i.strip().lower() for i in input_raw.split(',') if i.strip()]

# Grams input (Quantitative requirement from your proposal)
gram_map = {}
if ingredient_list:
    for ing in ingredient_list:
        gram_map[ing] = st.sidebar.number_input(f"Grams of {ing}", min_value=0.0, value=20.0)

analyze_clicked = st.sidebar.button("Analyze & Predict")

# --- 4. MAIN CONTENT ---
st.title("FoodLens: AI Health Impact Analysis")

if analyze_clicked:
    if not ingredient_list:
        st.warning("Please enter at least one ingredient.")
    else:
        # 1. Initialize DB Connection
        # Replace 'your_password' with your actual Neo4j password
        db = FoodLensDB("bolt://localhost:7687", "neo4j", "your_password")
        
        try:
            # 2. Fetch Data (This creates df_results)
            df_results = db.get_weighted_risks(gram_map)

            if not df_results.empty:
                col1, col2 = st.columns([1, 1.5])
                
                with col1:
                    st.subheader("⚠️ High Probability Risks")
                    # Grouping helps show "Likely to happen" diseases first
                    summary = df_results.groupby('disease')['score'].sum().sort_values(ascending=False)
                    for disease, score in summary.items():
                        st.markdown(f"**{disease.upper()}** (Risk Score: {score})")

                with col2:
                    st.subheader("Interactive Knowledge Graph")
                    nt = Network(height='450px', width='100%', bgcolor="#ffffff", font_color='black')
                    for _, row in df_results.iterrows():
                        nt.add_node(row['ingredient'], label=row['ingredient'], color='#004e92')
                        nt.add_node(row['disease'], label=row['disease'], color='#e63946')
                        nt.add_edge(row['ingredient'], row['disease'], value=row['score'])
                    
                    nt.save_graph('kg_graph.html')
                    components.html(open('kg_graph.html', 'r').read(), height=470)
                
                st.write("### Research Data Source")
                st.dataframe(df_results)
            else:
                st.info("No significant health risks found for these ingredient quantities.")
        
        except Exception as e:
            st.error(f"Error connecting to Neo4j: {e}")
        
        finally:
            db.close()
else:
    st.info("👈 Enter ingredients and grams in the sidebar to run the GNN prediction.")
