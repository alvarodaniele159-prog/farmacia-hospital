import streamlit as st
import json
import gspread
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Farmacia Hospital", layout="wide")

# CSS Ajustado para centrar y dar forma de tarjeta real
st.markdown("""
    <style>
    /* Centrar todo el contenido de la página */
    .block-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding-top: 5rem;
    }
    
    /* Estilo de los botones (Tarjetas) */
    div.stButton > button {
        background-color: #E0E0E0;
        color: #000000;
        height: 180px; /* Un poco más altos */
        width: 250px;  /* Ancho fijo para que parezcan tarjetas */
        border-radius: 25px;
        border: none;
        font-size: 22px;
        font-weight: bold;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3); /* Sombra para profundidad */
        transition: 0.3s;
        margin: 10px;
    }

    div.stButton > button:hover {
        background-color: #FFFFFF;
        transform: translateY(-10px); /* Se eleva un poquito al pasar el mouse */
        box-shadow: 0px 8px 25px rgba(0,0,0,0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# Lógica de Navegación
if 'menu' not in st.session_state:
    st.session_state.menu = "inicio"

if st.session_state.menu == "inicio":
    # Usamos columnas pero con un truco para centrarlas en el medio de la pantalla
    empty1, col1, col2, col3, empty2 = st.columns([1, 2, 2, 2, 1])
    
    with col1:
        if st.button("CARGA\n\n➕"):
            st.session_state.menu = "carga"
            st.rerun()
    with col2:
        if st.button("STOCK\n\n📋"):
            st.session_state.menu = "stock"
            st.rerun()
    with col3:
        if st.button("DESCARGA\n\n⬇️"):
            st.session_state.menu = "descarga"
            st.rerun()