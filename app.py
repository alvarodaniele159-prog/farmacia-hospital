import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
import json

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Gestión Hospital", layout="wide")

# 2. CONEXIÓN A GOOGLE SHEETS
@st.cache_resource
def conectar_sheets():
    try:
        credenciales_dict = json.loads(st.secrets["google_credentials"])
        gc = gspread.service_account_from_dict(credenciales_dict)
    except:
        gc = gspread.service_account(filename='credenciales.json')
    
    sh = gc.open("Inventario Farmacia Hospital")
    return sh.sheet1

hoja = conectar_sheets()

# 3. NAVEGACIÓN
if 'menu' not in st.session_state:
    st.session_state.menu = "inicio"

# ==========================================
# --- PANTALLA DE INICIO (Diseño Aislado) ---
# ==========================================
if st.session_state.menu == "inicio":
    # CSS Exclusivo para el menú principal
    st.markdown("""
        <style>
        .block-container {
            display: flex; flex-direction: column; justify-content: center; align-items: center; padding-top: 5rem;
        }
        div.stButton > button {
            background-color: #E0E0E0; color: #000000; height: 180px; width: 250px;
            border-radius: 25px; border: none; font-size: 22px; font-weight: bold;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.3); transition: 0.3s; margin: 10px;
        }
        div.stButton > button:hover { background-color: #FFFFFF; transform: translateY(-10px); }
        </style>
        """, unsafe_allow_html=True)

    st.title("🏥 Sistema de Farmacia")
    st.write("#")
    
    # Restauramos las columnas exactas que centraban tu diseño
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

# ==========================================
# --- PANTALLA DE CARGA (Diseño Aislado) ---
# ==========================================
elif st.session_state.menu == "carga":
    # CSS Exclusivo para formularios (restablece los botones a la normalidad)
    st.markdown("""
        <style>
        .block-container { padding-top: 2rem; }
        div.stButton > button {
            height: auto; width: auto; padding: 10px 20px; border-radius: 8px; font-weight: normal;
        }
        </style>
        """, unsafe_allow_html=True)

    st.title("📝 Registro de Medicamentos")
    
    if st.button("⬅️ Volver al Menú principal"):
        st.session_state.menu = "inicio"
        st.rerun()

    tab1, tab2 = st.tabs(["Carga Manual", "Carga Masiva (Excel)"])

    with tab1:
        with st.form("form_carga", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                nombre = st.text_input("Nombre del Medicamento")
                lote = st.text_input("Número de Lote")
            with col_b:
                cantidad = st.number_input("Cantidad", min_value=1, step=1)
                vencimiento = st.date_input("Fecha de Vencimiento")
            
            btn_guardar = st.form_submit_button("Guardar Individual")

        if btn_guardar:
            if nombre and lote:
                datos_actuales = hoja.get_all_records()
                nuevo_id = 1 if not datos_actuales else int(pd.DataFrame(datos_actuales)['id'].max()) + 1
                nueva_fila = [nuevo_id, nombre, lote, cantidad, str(vencimiento), "Farmacia Central"]
                hoja.append_row(nueva_fila)
                st.success(f"✅ {nombre} guardado.")
                st.rerun()

    with tab2:
        st.markdown("### Subir archivo Excel")
        st.info("El Excel debe tener los títulos exactos: Nombre, Lote, Vencimiento, Cantidad")
        
        archivo_subido = st.file_uploader("Selecciona el archivo Excel", type=["xlsx", "xls"])
        
        if archivo_subido is not None:
            try:
                df_excel = pd.read_excel(archivo_subido)
                df_excel.columns = df_excel.columns.str.strip()
                st.write("Vista previa de los datos a cargar:")
                st.dataframe(df_excel)

                if st.button("Confirmar Carga Masiva", type="primary"):
                    datos_actuales = hoja.get_all_records()
                    ultimo_id = 1 if not datos_actuales else int(pd.DataFrame(datos_actuales)['id'].max()) + 1
                    
                    filas_a_subir = []
                    for i, fila in df_excel.iterrows():
                        nueva_fila = [
                            ultimo_id + i, 
                            str(fila['Nombre']), 
                            str(fila['Lote']), 
                            int(fila['Cantidad']), 
                            pd.to_datetime(fila['Vencimiento']).strftime('%Y-%m-%d'), 
                            "Farmacia Central"
                        ]
                        filas_a_subir.append(nueva_fila)
                    
                    hoja.append_rows(filas_a_subir)
                    st.success(f"🚀 ¡Éxito! Se cargaron {len(filas_a_subir)} medicamentos nuevos.")
                    st.rerun()
            except KeyError as e:
                st.error(f"❌ Error: No se encontró la columna {e}. Revisa que los títulos en el Excel estén bien escritos.")
            except Exception as e:
                st.error(f"❌ Error al procesar el Excel. Detalle técnico: {e}")

    st.markdown("---")
    datos = hoja.get_all_records()
    if datos:
        st.subheader("📋 Últimos registros en la nube")
        st.table(pd.DataFrame(datos).tail(10))

# ==========================================
# --- PANTALLAS VACÍAS (Stock y Descarga) ---
# ==========================================
elif st.session_state.menu == "stock":
    # Aquí también restablecemos el estilo por las dudas
    st.markdown("<style>.block-container { padding-top: 2rem; }</style>", unsafe_allow_html=True)
    st.title("📋 Stock de Farmacia")
    if st.button("⬅️ Volver al Menú principal"):
        st.session_state.menu = "inicio"
        st.rerun()
    st.info("Aquí pondremos la tabla de stock con los colores de vencimiento.")

elif st.session_state.menu == "descarga":
    st.markdown("<style>.block-container { padding-top: 2rem; }</style>", unsafe_allow_html=True)
    st.title("⬇️ Retiro de Medicamentos")
    if st.button("⬅️ Volver al Menú principal"):
        st.session_state.menu = "inicio"
        st.rerun()
    st.info("Aquí pondremos la lógica para descontar del stock.")