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
    initial_sidebar_state="expanded" # This forces the sidebar to be open on load
)

def apply_custom_style():
    st.markdown("""
    <style>
    /* Ensure the header (which contains the sidebar toggle) is visible */
    header {visibility: visible !important;}
    .stAppDeployButton {display:none;}
    footer {visibility: hidden;}

    /* Professional Dark Background */
    .stApp {
        background: linear-gradient(rgba(15, 23, 42, 0.6), rgba(15, 23, 42, 0.75)), 
                    url('https://images.pexels.com/photos/1565982/pexels-photo-1565982.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(12px);
    }
    
    /* BLUE SIDEBAR HEADER - Your requested style */
    [data-testid="stSidebar"] h2 {
        color: #0000FF !important; 
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Gram Input Labels in Sidebar */
    [data-testid="stSidebar"] label p {
        color: #000000 !important;
        font-weight: bold;
    }

    /* Risk Cards with BLACK Font */
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

    /* Button with Hover Effect */
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background-color: #004e92;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px;
        margin-top: 20px;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #4CCD99 !important;
        color: #000000 !important;
        transform: translateY(-2px);
    }

    /* Global Header Styling */
    h1, h2, h4 { color: white !important; font-weight: 800 !important; }
    h3 { color: #4CCD99 !important; font-weight: 700 !important; }
    .stAlert p { color: #000000 !important; font-weight: 600; }
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

# DYNAMIC GRAM INPUTS (From your proposal requirements)
gram_map = {}
if input_ing:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Specify Grams")
    for ing in input_ing:
        gram_map[ing] = st.sidebar.number_input(f"Grams of {ing}", min_value=0.0, value=10.0, step=1.0)

analyze_clicked = st.sidebar.button("Analyze & Explain")

# --- 4. MAIN CONTENT ---
st.markdown("### FoodLens: Best way to find health effects with your foods 🤓")
st.markdown("#### Evidence-Based Research & Ingredient Safety")
st.divider()

if analyze_clicked:
    if df_triplets is not None:
        # Filtering logic
        relevant = df_triplets[df_triplets['ingredient'].str.lower().isin(input_ing)]

        if not relevant.empty:
            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.subheader("⚠️ Health Risk Predictions")
                
                # Logic: We only show the top 5 most frequent diseases to avoid the "10+ diseases" clutter
                top_diseases = relevant['disease'].value_counts().head(5).index
                
                for d in top_diseases:
                    st.markdown(f'<div class="risk-card">{d}</div>', unsafe_allow_html=True)
                
                st.info(f"Analyzed {len(input_ing)} ingredients based on {len(relevant)} evidence links.")

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
        else:
            st.warning("No risks found in our database for these ingredients.")
    else:
        st.error("Dataset 'pubmed_triplets.csv' not found.")
else:
    st.info("👈 Enter ingredients in the sidebar and specify their weights to begin.")
