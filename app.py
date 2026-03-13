import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# Configuración de la página
st.set_page_config(page_title="Gestión de Stock - Hospital", layout="wide")

st.title("☁️ Sistema de Inventario en la Nube")
st.markdown("---")

# 1. CONEXIÓN INTELIGENTE (Local y Nube)
@st.cache_resource
def conectar_sheets():
    try:
        # Modo Nube: Intenta usar las llaves secretas de Streamlit Cloud
        credenciales = dict(st.secrets["gcp_service_account"])
        gc = gspread.service_account_from_dict(credenciales)
    except Exception:
        # Modo Local: Si no está en la nube, usa tu archivo local
        gc = gspread.service_account(filename='credenciales.json')
        
    sh = gc.open("Inventario Farmacia Hospital")
    return sh.sheet1

hoja = conectar_sheets()

# ... (DE AQUÍ PARA ABAJO, EL CÓDIGO SIGUE EXACTAMENTE IGUAL A COMO LO TENÍAS) ...
# def obtener_datos():
#     datos = hoja.get_all_records()

# 2. OBTENER DATOS EN TIEMPO REAL
def obtener_datos():
    datos = hoja.get_all_records()
    if not datos:
        # Si está vacía, armamos la estructura de las columnas
        return pd.DataFrame(columns=['id', 'nombre', 'lote', 'cantidad', 'vencimiento', 'sector'])
    return pd.DataFrame(datos)

def procesar_alertas(df):
    if df.empty:
        return df, 0, 0
    
    df['vencimiento'] = pd.to_datetime(df['vencimiento']).dt.date
    hoy = datetime.now().date()
    estados = []
    vencidos_count = proximos_count = 0
    
    for fecha in df['vencimiento']:
        dias_restantes = (fecha - hoy).days
        if dias_restantes < 0:
            estados.append("🔴 Vencido")
            vencidos_count += 1
        elif dias_restantes <= 30:
            estados.append("🟡 Próximo a Vencer")
            proximos_count += 1
        else:
            estados.append("🟢 Óptimo")
            
    df.insert(0, 'Estado', estados)
    return df, vencidos_count, proximos_count

# --- SECCIÓN CENTRAL: VISTA DE LA BODEGA ---
df_stock = obtener_datos()

if df_stock.empty:
    st.warning("Tu Google Sheet está vacío. ¡Carga el primer medicamento!")
else:
    datos_procesados, vencidos, proximos = procesar_alertas(df_stock.copy())
    
    if vencidos > 0:
        st.error(f"🚨 Hay {vencidos} lote(s) VENCIDO(S).")
    if proximos > 0:
        st.warning(f"⚠️ Hay {proximos} lote(s) próximos a vencer.")
        
    st.subheader("📦 Stock Actual en la Nube")
    
    busqueda = st.text_input("🔍 Buscar medicamento:")
    if busqueda:
        datos_procesados = datos_procesados[
            datos_procesados['nombre'].str.contains(busqueda, case=False, na=False) |
            datos_procesados['lote'].astype(str).str.contains(busqueda, case=False, na=False)
        ]

    st.dataframe(datos_procesados, use_container_width=True)

# --- MENÚ LATERAL: ACCIONES EN LA NUBE ---
with st.sidebar:
    st.header("⚙️ Gestión de Inventario")
    
    # RETIRAR STOCK
    st.subheader("➖ Retirar Medicamento")
    if not df_stock.empty:
        with st.form("form_egreso"):
            opciones = df_stock['id'].astype(str) + " | " + df_stock['nombre'] + " (Lote: " + df_stock['lote'].astype(str) + ")"
            seleccion = st.selectbox("Seleccionar Medicamento a retirar:", opciones)
            cantidad_retirar = st.number_input("Cantidad a retirar", min_value=1, step=1)
            btn_retirar = st.form_submit_button("Confirmar Retiro")
            
            if btn_retirar:
                id_seleccionado = int(seleccion.split(" | ")[0])
                # Buscamos la información actual
                med = df_stock[df_stock['id'] == id_seleccionado].iloc[0]
                stock_actual = int(med['cantidad'])
                
                if cantidad_retirar > stock_actual:
                    st.error(f"❌ Error: Solo hay {stock_actual} unidades.")
                else:
                    nuevo_stock = stock_actual - cantidad_retirar
                    # Buscar la fila exacta en el Excel de Google y actualizarla
                    # (La columna 4 es la de cantidad)
                    celda = hoja.find(str(id_seleccionado), in_column=1)
                    if celda:
                        hoja.update_cell(celda.row, 4, nuevo_stock)
                        st.success(f"✅ Se retiraron {cantidad_retirar}. Quedan {nuevo_stock}.")
                        st.rerun()
    
    st.markdown("---")

    # CARGAR NUEVO LOTE
    st.subheader("➕ Cargar Nuevo Lote")
    with st.form("nuevo_remedio"):
        nombre = st.text_input("Nombre")
        lote = st.text_input("Lote")
        cantidad = st.number_input("Cantidad", min_value=0, step=1)
        vencimiento = st.date_input("Vencimiento")
        sector = st.selectbox("Sector", ["Farmacia Central", "Emergencias", "Pediatría", "UTI"])
        
        btn_guardar = st.form_submit_button("Subir a la Nube")
        
        if btn_guardar:
            if nombre and lote:
                if not df_stock.empty and str(lote) in df_stock['lote'].astype(str).values:
                    st.error("❌ Ese lote ya existe.")
                else:
                    # Generamos un ID único y guardamos la fila
                    nuevo_id = 1 if df_stock.empty else int(df_stock['id'].max()) + 1
                    nueva_fila = [nuevo_id, nombre, lote, cantidad, str(vencimiento), sector]
                    hoja.append_row(nueva_fila)
                    st.success("✅ Guardado exitosamente en Google Sheets.")
                    st.rerun()
            else:
                st.warning("⚠️ Completa Nombre y Lote.")