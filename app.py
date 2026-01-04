import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import os

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(
    page_title="FoodLens | Health Effects Finder", 
    page_icon="🥗", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

def apply_custom_style():
    st.markdown("""
    <style>
    header {visibility: visible !important;}
    .stAppDeployButton {display:none;}
    footer {visibility: hidden;}

    .stApp {
        background: linear-gradient(rgba(15, 23, 42, 0.6), rgba(15, 23, 42, 0.75)), 
                    url('https://images.pexels.com/photos/1565982/pexels-photo-1565982.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2');
        background-size: cover; background-position: center; background-attachment: fixed;
    }

    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(12px);
    }
    
    [data-testid="stSidebar"] h2 {
        color: #0000FF !important; 
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .risk-card {
        background: #8CE4FF; 
        border-left: 8px solid #e63946;
        padding: 1.2rem;
        border-radius: 15px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        margin-bottom: 12px;
        color: #000000 !important; 
        font-weight: bold;
        text-transform: uppercase;
    }

    .stButton>button {
        width: 100%; border-radius: 20px; background-color: #004e92;
        color: white; font-weight: bold; padding: 10px; margin-top: 20px;
    }

    h1, h2, h4 { color: white !important; font-weight: 800 !important; }
    h3 { color: #4CCD99 !important; font-weight: 700 !important; }
    
    /* Styling for the dataframe table background */
    [data-testid="stDataFrame"] {
        background: rgba(255, 255, 255, 0.9);
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# --- 2. DATA LOADING ---
@st.cache_data
def load_data():
    if not os.path.exists('pubmed_triplets.csv'):
        return None
    try:
        df = pd.read_csv('pubmed_triplets.csv', on_bad_lines='skip')
        df.columns = [c.lower().strip() for c in df.columns]
        return df
    except:
        return None

df_triplets = load_data()

# --- 3. SIDEBAR ---
st.sidebar.image("https://images.unsplash.com/photo-1543339308-43e59d6b73a6?w=400", use_container_width=True)
st.sidebar.header("Input Food Label")

input_raw = st.sidebar.text_area("Enter Ingredients (Comma Separated)", placeholder="e.g., alcohol, sugar", height=100)
input_ing = [i.strip().lower() for i in input_raw.split(',') if i.strip()]

gram_map = {}
if input_ing:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Specify Grams")
    for ing in input_ing:
        gram_map[ing] = st.sidebar.number_input(f"Grams of {ing}", min_value=0.0, value=10.0, step=1.0)

analyze_clicked = st.sidebar.button("Analyze & Explain")

# --- 4. MAIN CONTENT ---
st.markdown("### FoodLens: Knowledge Graph Health Predictor 🤓")
st.divider()

if analyze_clicked:
    if df_triplets is not None:
        relevant = df_triplets[df_triplets['ingredient'].str.lower().isin(input_ing)]

        if not relevant.empty:
            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.subheader("⚠️ Health Risk Predictions")
                top_diseases = relevant['disease'].value_counts().head(5).index
                for d in top_diseases:
                    st.markdown(f'<div class="risk-card">{d}</div>', unsafe_allow_html=True)
                st.info(f"Analyzed {len(input_ing)} ingredients.")

            with col2:
                st.subheader("🕸️ Interactive Knowledge Graph")
                nt = Network(height='450px', width='100%', bgcolor="#ffffff", font_color='#101820')
                nt.force_atlas_2based() 
                for _, row in relevant.iterrows():
                    i_node = str(row['ingredient']).title()
                    d_node = str(row['disease']).title()
                    nt.add_node(i_node, label=i_node, color='#004e92', size=25)
                    nt.add_node(d_node, label=d_node, color='#e63946', size=20)
                    nt.add_edge(i_node, d_node, color='#94a3b8')
                
                nt.save_graph('kg_graph.html')
                components.html(open('kg_graph.html', 'r').read(), height=470)
            
            # --- NEW SECTION: RESEARCH TABLE WITH LINKS ---
            st.divider()
            st.subheader("📚 Evidence & Research Sources")
            
            # Cleaning the dataframe for display
            display_df = relevant.copy()
            display_df['ingredient'] = display_df['ingredient'].str.title()
            display_df['disease'] = display_df['disease'].str.title()
            
            # Logic for Clickable Table
            # Assumes your CSV has a column named 'url' or 'pubmed_url'
            # If your column is named differently, change 'url' below to your column name
            url_column = 'url' if 'url' in display_df.columns else display_df.columns[-1] 

            st.dataframe(
                display_df,
                column_config={
                    url_column: st.column_config.LinkColumn(
                        "PubMed Source",
                        help="Click to view the scientific paper",
                        validate=r"^https://",
                        display_text="View Research 📄"
                    ),
                    "ingredient": "Ingredient",
                    "disease": "Predicted Impact"
                },
                hide_index=True,
                use_container_width=True
            )

        else:
            st.warning("No risks found in our database for these ingredients.")
    else:
        st.error("Dataset 'pubmed_triplets.csv' not found.")
else:
    st.info("👈 Enter ingredients in the sidebar and specify their weights to begin.")
