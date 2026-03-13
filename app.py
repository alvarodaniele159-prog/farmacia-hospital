import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
import json

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Gestión Hospital", layout="wide")

# (Mantenemos tu CSS de los botones para que el inicio siga igual)
st.markdown("""
    <style>
    .block-container { display: flex; flex-direction: column; align-items: center; }
    div.stButton > button {
        background-color: #E0E0E0; color: #000000; height: 180px; width: 250px;
        border-radius: 25px; border: none; font-size: 22px; font-weight: bold;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3); transition: 0.3s; margin: 10px;
    }
    div.stButton > button:hover { background-color: #FFFFFF; transform: translateY(-10px); }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN A GOOGLE SHEETS
@st.cache_resource
def conectar_sheets():
    try:
        # Intenta leer desde Secrets (Nube)
        credenciales_dict = json.loads(st.secrets["google_credentials"])
        gc = gspread.service_account_from_dict(credenciales_dict)
    except:
        # Usa archivo local (PC)
        gc = gspread.service_account(filename='credenciales.json')
    
    sh = gc.open("Inventario Farmacia Hospital")
    return sh.sheet1

hoja = conectar_sheets()

# 3. NAVEGACIÓN
if 'menu' not in st.session_state:
    st.session_state.menu = "inicio"

# --- PANTALLA DE INICIO ---
if st.session_state.menu == "inicio":
    st.title("🏥 Sistema de Farmacia")
    st.write("#")
    col1, col2, col3 = st.columns(3)
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

# --- PANTALLA DE CARGA ---
elif st.session_state.menu == "carga":
    st.title("📝 Registro de Medicamentos")
    
    if st.button("⬅️ Volver al Menú"):
        st.session_state.menu = "inicio"
        st.rerun()

    # Formulario de entrada
    with st.container():
        st.markdown("### Ingrese los datos del nuevo lote")
        with st.form("form_carga", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                nombre = st.text_input("Nombre del Medicamento")
                lote = st.text_input("Número de Lote")
            with col_b:
                cantidad = st.number_input("Cantidad", min_value=1, step=1)
                vencimiento = st.date_input("Fecha de Vencimiento")
            
            btn_guardar = st.form_submit_button("Guardar en Inventario")

        if btn_guardar:
            if nombre and lote:
                # Obtenemos datos actuales para generar el ID
                datos_actuales = hoja.get_all_records()
                df_temp = pd.DataFrame(datos_actuales)
                nuevo_id = 1 if df_temp.empty else int(df_temp['id'].max()) + 1
                
                # Preparamos la fila y la mandamos a Google Sheets
                nueva_fila = [nuevo_id, nombre, lote, cantidad, str(vencimiento), "Farmacia Central"]
                hoja.append_row(nueva_fila)
                st.success(f"✅ {nombre} (Lote: {lote}) guardado correctamente.")
            else:
                st.error("⚠️ Por favor completa el Nombre y el Lote.")

    st.markdown("---")
    
    # Lista de lo que hay en el sistema (debajo del formulario)
    st.subheader("📋 Últimos registros cargados")
    datos = hoja.get_all_records()
    if datos:
        df_mostrar = pd.DataFrame(datos)
        # Mostramos los últimos 10 cargados (al final de la lista)
        st.table(df_mostrar.tail(10)) 
    else:
        st.info("Aún no hay medicamentos cargados.")