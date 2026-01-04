import streamlit as st
import pandas as pd
import os
from pyvis.network import Network
import streamlit.components.v1 as components

# 1. FORCE SIDEBAR OPEN HERE
st.set_page_config(
    page_title="FoodLens | Health Effects Finder", 
    page_icon="🥗", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# 2. UPDATED CSS (Removed the header hiding)
def apply_custom_style():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(15, 23, 42, 0.6), rgba(15, 23, 42, 0.75)), 
                    url('https://images.pexels.com/photos/1565982/pexels-photo-1565982.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2');
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    [data-testid="stSidebar"] { background: rgba(255, 255, 255, 0.8) !important; }
    [data-testid="stSidebar"] h2 { color: #0000FF !important; } /* BLUE HEADER */
    .risk-card { background: #8CE4FF; padding: 1rem; border-radius: 10px; color: black; font-weight: bold; margin-bottom: 5px;}
    </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# 3. DATA LOADING
@st.cache_data
def load_data():
    if os.path.exists('pubmed_triplets.csv'):
        return pd.read_csv('pubmed_triplets.csv')
    return None

df = load_data()

# 4. SIDEBAR
st.sidebar.header("Input Food Label")
input_raw = st.sidebar.text_area("Ingredients", "sugar, alcohol")
analyze_btn = st.sidebar.button("Analyze")

# 5. MAIN LOGIC & "TOO MANY DISEASES" FIX
if analyze_btn and df is not None:
    input_ing = [i.strip().lower() for i in input_raw.split(',') if i.strip()]
    relevant = df[df['ingredient'].str.lower().isin(input_ing)]
    
    if not relevant.empty:
        # To avoid showing 10+ diseases, we take the top 5 most frequent/relevant
        display_diseases = relevant['disease'].value_counts().head(5).index
        
        col1, col2 = st.columns([1, 1.5])
        with col1:
            st.subheader("Top Risk Predictions")
            for d in display_diseases:
                st.markdown(f'<div class="risk-card">{d}</div>', unsafe_allow_html=True)
        
        with col2:
            st.subheader("Knowledge Graph")
            # Graph generation code...
    else:
        st.warning("No matches found.")
        
