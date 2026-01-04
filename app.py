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
    layout="wide"
)

def apply_custom_style():
    """Applies professional CSS including dark background and fixed font colors."""
    st.markdown("""
    <style>
    /* 1. Professional Dark Background with Food Image */
    .stApp {
        background: linear-gradient(rgba(15, 23, 42, 0.6), rgba(15, 23, 42, 0.85)), 
                    url('https://images.pexels.com/photos/1565982/pexels-photo-1565982.jpeg?cs=srgb&dl=bread-color-copyspace-1565982.jpg&fm=jpg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* 2. Fix the Info Box (st.info) font color to BLACK */
    .stAlert {
        background-color: rgba(248, 250, 252, 0.9) !important;
        border: none;
        border-radius: 12px;
    }
    .stAlert p {
        color: #000000 !important;
        font-weight: 600;
    }

    /* 3. Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.3);
    }

    /* 4. Professional Risk Cards with BLACK Font */
    .risk-card {
        background: #8CE4FF; /* Your light blue color */
        border-left: 8px solid #e63946;
        padding: 1.2rem;
        border-radius: 15px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        margin-bottom: 12px;
        transition: transform 0.2s ease-in-out;
        
        /* Force Black Font */
        color: #000000 !important; 
        font-family: sans-serif;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.85rem;
    }

    .risk-card:hover {
        transform: translateY(-3px);
        background: #FFFFFF;
    }
    
    /* 5. Global Text & Header Styling (White for contrast) */
    h1,h3,h4 {
        color: white !important;
        font-weight: 800 !important;
    }
    h2{
        color:#4CCD99 !important ;     
    }
                
    /* 6. Professional Button */
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        background-color: #004e92;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px;
        margin:20px;
    }
    .stButton>button:hover {
        background-color: #836FFF !important; /* Changes to your h3 color on hover */
        color: #000000 !important; /* Text turns black for contrast */
        transform: translateY(-2px); /* Lifts the button slightly */
        box-shadow: 0 8px 15px rgba(76, 205, 153, 0.4); /* Adds a green glow */
        border: none;
    }
     /* 2. Style the Sidebar Header (st.sidebar.header) */
    [data-testid="stSidebar"] h2 {
        color: black !important; /* Mint Green to match your subheaders */
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    </style>
    """, unsafe_allow_html=True)

# Apply styling immediately
apply_custom_style()

# --- 2. DATA LOADING ---
@st.cache_data
def load_data():
    try:
        if not os.path.exists('pubmed_triplets.csv'):
            return None
        with open('pubmed_triplets.csv', 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        data = []
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) >= 3:
                ing = parts[0].replace('"', '').lower().strip()
                dis = parts[2].replace('"', '').lower().strip()
                if ing == 'ingredient' or not ing: 
                    continue
                data.append({
                    "ingredient": ing, 
                    "disease": dis, 
                    "pubmed_url": parts[5].replace('"', '') if len(parts) > 5 else ""
                })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

df_triplets = load_data()

# --- 3. SIDEBAR ---
st.sidebar.image("OIP.jpg", width=800)
st.sidebar.header("Input Food Label")
input_raw = st.sidebar.text_area("Enter Ingredients", placeholder="e.g., alcohol, sugar", height=150)
analyze_clicked = st.sidebar.button("Analyze & Explain")

# --- 4. MAIN CONTENT ---
st.markdown("## FoodLens: Best way to find health effects with your foods🤓")
st.markdown("#### Evidence-Based Research & Ingredient Safety")
st.divider()

if analyze_clicked:
    if df_triplets is not None:
        input_ing = [i.strip().lower() for i in input_raw.split(',') if i.strip()]
        relevant = df_triplets[df_triplets['ingredient'].isin(input_ing)]

        if not relevant.empty:
            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.subheader("⚠️ Health Risk Predictions")
                unique_diseases = relevant['disease'].unique()
                for d in unique_diseases:
                    st.markdown(f'<div class="risk-card">{d}</div>', unsafe_allow_html=True)
                
                # The Info box that now has Black Text
                st.info(f"Analyzed {len(input_ing)} ingredients. Found {len(relevant)} research connections.")

            with col2:
                st.subheader("🕸️ Interactive Knowledge Graph")
                nt = Network(height='450px', width='100%', bgcolor="#ffffff", font_color='#101820')
                nt.force_atlas_2based() 
                for _, row in relevant.iterrows():
                    nt.add_node(row['ingredient'].title(), label=row['ingredient'].title(), color='#004e92', size=25)
                    nt.add_node(row['disease'].title(), label=row['disease'].title(), color='#e63946', size=20)
                    nt.add_edge(row['ingredient'].title(), row['disease'].title(), color='#94a3b8')
                nt.save_graph('kg_graph.html')
                components.html(open('kg_graph.html', 'r').read(), height=470)

            st.subheader("🔍 Research Evidence (Ground Truth)")
            st.dataframe(relevant, use_container_width=True)
    else:
        st.error("Database file (pubmed_triplets.csv) not found.")
else:
    # This info box also has black text now
    st.info("👈 Enter ingredients in the sidebar (e.g., 'alcohol, peanuts') and click 'Analyze' to begin.")