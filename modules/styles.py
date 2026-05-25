
# modules/styles.py
import streamlit as st

# Colores de marca minimalistas
COLOR_PRIMARY = "#900C3F"
TEXT_COLOR = "#2C3E50"
BACKGROUND = "#FFFFFF"

def apply_styles():
    st.markdown(f"""
        <style>
            .stApp {{ background-color: {BACKGROUND}; color: {TEXT_COLOR}; }}
            h1, h2, h3 {{ color: {COLOR_PRIMARY} !important; font-family: 'Helvetica Neue', sans-serif; }}
            .stButton>button {{ background-color: {COLOR_PRIMARY}; color: white !important; border-radius: 4px; border: none; }}
            .stButton>button:hover {{ background-color: #581845; color: white !important; }}
            p, .stMarkdown, label, .stSelectbox, .stNumberInput, .stTextInput {{ color: {TEXT_COLOR} !important; }}
            .stDataFrame table {{ color: {TEXT_COLOR} !important; }}
            /* Asegurar que las etiquetas de Markdown también sean visibles */
            .stMarkdown p strong {{ color: {TEXT_COLOR}; }}
            
            /* FIX CRÍTICO: FORZAR EL COLOR DE LOS VALORES DE ST.METRIC */
            div[data-testid="stMetricValue"] {{
                color: {TEXT_COLOR} !important;
            }}
        </style>
    """, unsafe_allow_html=True)
