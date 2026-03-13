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
# --- PANTALLA DE INICIO ---
# ==========================================
if st.session_state.menu == "inicio":
    st.markdown("""
        <style>
        .block-container { display: flex; flex-direction: column; justify-content: center; align-items: center; padding-top: 5rem; }
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
# --- PANTALLA DE CARGA (Con lógica UPSERT) ---
# ==========================================
elif st.session_state.menu == "carga":
    st.markdown("<style>.block-container { padding-top: 2rem; } div.stButton > button { height: auto; width: auto; padding: 10px 20px; border-radius: 8px; }</style>", unsafe_allow_html=True)

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
                df_actual = pd.DataFrame(datos_actuales)
                
                # Preparamos los datos para comparar (minúsculas y sin espacios extra)
                n_match = str(nombre).strip().lower()
                l_match = str(lote).strip().lower()
                v_match = str(vencimiento)

                # Buscamos si ya existe
                if not df_actual.empty:
                    filtro = (
                        (df_actual['nombre'].astype(str).str.strip().str.lower() == n_match) &
                        (df_actual['lote'].astype(str).str.strip().str.lower() == l_match) &
                        (df_actual['vencimiento'].astype(str).str.strip() == v_match)
                    )
                    coincidencias = df_actual[filtro]
                else:
                    coincidencias = pd.DataFrame()

                # Si el lote ya existe, SUMAMOS. Si no, AGREGAMOS.
                if not coincidencias.empty:
                    # Obtenemos el número de fila exacto en el Excel de Google
                    indice_df = coincidencias.index[0]
                    fila_google_sheets = int(indice_df) + 2 # +1 por índice 0, +1 por la cabecera
                    
                    stock_previo = int(coincidencias.iloc[0]['cantidad'])
                    nuevo_stock = stock_previo + cantidad
                    
                    # Actualizamos solo la celda de la cantidad (Columna 4)
                    hoja.update_cell(fila_google_sheets, 4, nuevo_stock)
                    st.success(f"🔄 Lote existente encontrado. Se sumaron {cantidad} a {nombre}. Stock total: {nuevo_stock}")
                else:
                    nuevo_id = 1 if df_actual.empty else int(df_actual['id'].max()) + 1
                    nueva_fila = [nuevo_id, nombre, lote, cantidad, str(vencimiento), "Farmacia Central"]
                    hoja.append_row(nueva_fila)
                    st.success(f"✅ Nuevo medicamento registrado: {nombre}.")
                
                st.rerun()

    with tab2:
        st.markdown("### Subir archivo Excel")
        st.info("Si el lote ya existe en el sistema, se sumará la cantidad automáticamente.")
        
        archivo_subido = st.file_uploader("Selecciona el archivo Excel", type=["xlsx", "xls"])
        
        if archivo_subido is not None:
            try:
                df_excel = pd.read_excel(archivo_subido)
                df_excel.columns = df_excel.columns.str.strip()
                st.write("Vista previa:")
                st.dataframe(df_excel)

                if st.button("Confirmar Carga Masiva", type="primary"):
                    datos_actuales = hoja.get_all_records()
                    df_actual = pd.DataFrame(datos_actuales)
                    ultimo_id = 1 if df_actual.empty else int(df_actual['id'].max())
                    
                    filas_nuevas = []
                    actualizaciones = 0
                    
                    # Revisamos el Excel fila por fila
                    for i, fila in df_excel.iterrows():
                        n_excel = str(fila['Nombre']).strip()
                        l_excel = str(fila['Lote']).strip()
                        v_excel = pd.to_datetime(fila['Vencimiento']).strftime('%Y-%m-%d')
                        c_excel = int(fila['Cantidad'])
                        
                        # Buscamos en la base de datos actual
                        if not df_actual.empty:
                            filtro = (
                                (df_actual['nombre'].astype(str).str.strip().str.lower() == n_excel.lower()) &
                                (df_actual['lote'].astype(str).str.strip().str.lower() == l_excel.lower()) &
                                (df_actual['vencimiento'].astype(str).str.strip() == v_excel)
                            )
                            coincidencia = df_actual[filtro]
                        else:
                            coincidencia = pd.DataFrame()

                        if not coincidencia.empty:
                            # Si existe, actualizamos la celda
                            idx = coincidencia.index[0]
                            fila_sheet = int(idx) + 2
                            stock_viejo = int(df_actual.at[idx, 'cantidad'])
                            nuevo_stock = stock_viejo + c_excel
                            
                            hoja.update_cell(fila_sheet, 4, nuevo_stock)
                            
                            # Actualizamos nuestra memoria para no duplicar si el Excel trae dos veces el mismo
                            df_actual.at[idx, 'cantidad'] = nuevo_stock
                            actualizaciones += 1
                        else:
                            # Si no existe, lo preparamos para guardarlo como fila nueva
                            ultimo_id += 1
                            nueva_fila = [ultimo_id, n_excel, l_excel, c_excel, v_excel, "Farmacia Central"]
                            filas_nuevas.append(nueva_fila)
                            
                            # Lo agregamos a la memoria por si se repite más abajo en el mismo Excel
                            nueva_fila_df = pd.DataFrame([{'id': ultimo_id, 'nombre': n_excel, 'lote': l_excel, 'cantidad': c_excel, 'vencimiento': v_excel, 'sector': 'Farmacia Central'}])
                            df_actual = pd.concat([df_actual, nueva_fila_df], ignore_index=True)
                    
                    # Mandamos las filas nuevas todas juntas al final
                    if filas_nuevas:
                        hoja.append_rows(filas_nuevas)
                        
                    st.success(f"🚀 ¡Completado! Se crearon {len(filas_nuevas)} lotes nuevos y se actualizaron {actualizaciones} lotes existentes.")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error al procesar el Excel. Detalle técnico: {e}")

    st.markdown("---")
    datos = hoja.get_all_records()
    if datos:
        st.subheader("📋 Últimos registros en la nube")
        st.table(pd.DataFrame(datos).tail(10))

# ==========================================
# --- PANTALLA DE DESCARGA (Retiros) ---
# ==========================================
elif st.session_state.menu == "descarga":
    # Restablecemos el estilo normal de los botones para esta pantalla
    st.markdown("<style>.block-container { padding-top: 2rem; } div.stButton > button { height: auto; width: auto; padding: 10px 20px; border-radius: 8px; }</style>", unsafe_allow_html=True)
    
    st.title("⬇️ Retiro de Medicamentos")
    
    if st.button("⬅️ Volver al Menú principal"):
        st.session_state.menu = "inicio"
        st.rerun()

    tab1, tab2 = st.tabs(["Descarga Individual", "Descarga Masiva (Excel)"])

    with tab1:
        st.markdown("### Seleccione el medicamento a retirar")
        
        # 1. Traemos los datos actuales de la base de datos
        datos_actuales = hoja.get_all_records()
        df_inventario = pd.DataFrame(datos_actuales)
        
        if df_inventario.empty:
            st.warning("⚠️ El inventario está vacío. No hay nada para retirar.")
        else:
            # 2. Filtramos para ocultar los medicamentos que ya están en 0 stock
            df_con_stock = df_inventario[df_inventario['cantidad'] > 0]
            
            if df_con_stock.empty:
                st.warning("⚠️ No hay medicamentos con stock disponible en este momento.")
            else:
                # 3. Creamos el buscador mágico de Streamlit (selectbox)
                # Extraemos los nombres únicos y los ordenamos alfabéticamente
                nombres_unicos = sorted(df_con_stock['nombre'].astype(str).str.strip().unique())
                med_seleccionado = st.selectbox("🔍 Buscar Medicamento (Escribe para filtrar)", options=["Seleccione una opción..."] + nombres_unicos)
                
                # 4. Lógica en cadena: Si eligen un medicamento, mostramos SUS lotes
                if med_seleccionado != "Seleccione una opción...":
                    df_filtrado = df_con_stock[df_con_stock['nombre'].str.strip() == med_seleccionado]
                    
                    opciones_lote = ["Seleccione el lote..."]
                    diccionario_lotes = {} # Usamos esto como "memoria secreta" para guardar la fila exacta
                    
                    # Armamos las opciones visuales para el usuario
                    for idx, fila in df_filtrado.iterrows():
                        texto_opcion = f"Lote: {fila['lote']} | Vence: {fila['vencimiento']} | Stock Actual: {fila['cantidad']}"
                        opciones_lote.append(texto_opcion)
                        
                        # Guardamos los datos técnicos vinculados a ese texto
                        diccionario_lotes[texto_opcion] = {
                            'indice_real': idx, 
                            'stock_actual': int(fila['cantidad']),
                            'nombre': fila['nombre'],
                            'lote': fila['lote']
                        }
                        
                    lote_seleccionado = st.selectbox("📦 Seleccionar Lote y Vencimiento", options=opciones_lote)
                    
                    # 5. Lógica final: Si eligen el lote, pedimos la cantidad y descontamos
                    if lote_seleccionado != "Seleccione el lote...":
                        datos_lote = diccionario_lotes[lote_seleccionado]
                        stock_maximo = datos_lote['stock_actual']
                        
                        # El número máximo que pueden retirar es el stock que hay (evita stock negativo)
                        cantidad_a_retirar = st.number_input("Cantidad a retirar", min_value=1, max_value=stock_maximo, step=1)
                        
                        if st.button("Confirmar Descarga", type="primary"):
                            # Calculamos la posición exacta en el Excel (+2 por el índice 0 y la cabecera)
                            fila_google = int(datos_lote['indice_real']) + 2
                            nuevo_stock = stock_maximo - cantidad_a_retirar
                            
                            # Actualizamos solo la celda de cantidad
                            hoja.update_cell(fila_google, 4, nuevo_stock)
                            
                            st.success(f"✅ ¡Éxito! Se retiraron {cantidad_a_retirar} unidades de {datos_lote['nombre']} (Lote: {datos_lote['lote']}). Quedan {nuevo_stock} en stock.")
                            st.rerun()

    with tab2:
        st.info("Aquí programaremos la descarga masiva con Excel cuando estés listo.")