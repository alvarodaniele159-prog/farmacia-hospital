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
# --- PANTALLA DE CARGA ---
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
                df_actual = pd.DataFrame(hoja.get_all_records())
                n_match = str(nombre).strip().lower()
                l_match = str(lote).strip().lower()
                v_match = str(vencimiento)

                if not df_actual.empty:
                    filtro = (df_actual['nombre'].astype(str).str.strip().str.lower() == n_match) & (df_actual['lote'].astype(str).str.strip().str.lower() == l_match) & (df_actual['vencimiento'].astype(str).str.strip() == v_match)
                    coincidencias = df_actual[filtro]
                else:
                    coincidencias = pd.DataFrame()

                if not coincidencias.empty:
                    indice_df = coincidencias.index[0]
                    fila_google_sheets = int(indice_df) + 2 
                    stock_previo = int(coincidencias.iloc[0]['cantidad'])
                    nuevo_stock = stock_previo + cantidad
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
        st.info("El Excel debe tener los títulos exactos: Nombre, Lote, Vencimiento, Cantidad")
        archivo_subido = st.file_uploader("Selecciona el archivo Excel", type=["xlsx", "xls"], key="carga_masiva")
        
        if archivo_subido is not None:
            try:
                df_excel = pd.read_excel(archivo_subido)
                df_excel.columns = df_excel.columns.str.strip()
                st.dataframe(df_excel)

                if st.button("Confirmar Carga Masiva", type="primary"):
                    df_actual = pd.DataFrame(hoja.get_all_records())
                    ultimo_id = 1 if df_actual.empty else int(df_actual['id'].max())
                    filas_nuevas = []
                    actualizaciones = 0
                    
                    for i, fila in df_excel.iterrows():
                        n_excel = str(fila['Nombre']).strip()
                        l_excel = str(fila['Lote']).strip()
                        v_excel = pd.to_datetime(fila['Vencimiento']).strftime('%Y-%m-%d')
                        c_excel = int(fila['Cantidad'])
                        
                        if not df_actual.empty:
                            filtro = (df_actual['nombre'].astype(str).str.strip().str.lower() == n_excel.lower()) & (df_actual['lote'].astype(str).str.strip().str.lower() == l_excel.lower()) & (df_actual['vencimiento'].astype(str).str.strip() == v_excel)
                            coincidencia = df_actual[filtro]
                        else:
                            coincidencia = pd.DataFrame()

                        if not coincidencia.empty:
                            idx = coincidencia.index[0]
                            nuevo_stock = int(df_actual.at[idx, 'cantidad']) + c_excel
                            hoja.update_cell(int(idx) + 2, 4, nuevo_stock)
                            df_actual.at[idx, 'cantidad'] = nuevo_stock
                            actualizaciones += 1
                        else:
                            ultimo_id += 1
                            filas_nuevas.append([ultimo_id, n_excel, l_excel, c_excel, v_excel, "Farmacia Central"])
                            df_actual = pd.concat([df_actual, pd.DataFrame([{'id': ultimo_id, 'nombre': n_excel, 'lote': l_excel, 'cantidad': c_excel, 'vencimiento': v_excel}])], ignore_index=True)
                    
                    if filas_nuevas:
                        hoja.append_rows(filas_nuevas)
                    st.success(f"🚀 Completado: {len(filas_nuevas)} lotes nuevos y {actualizaciones} actualizados.")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error al procesar: {e}")

# ==========================================
# --- PANTALLA DE DESCARGA ---
# ==========================================
elif st.session_state.menu == "descarga":
    st.markdown("<style>.block-container { padding-top: 2rem; } div.stButton > button { height: auto; width: auto; padding: 10px 20px; border-radius: 8px; }</style>", unsafe_allow_html=True)
    st.title("⬇️ Retiro de Medicamentos")
    
    if st.button("⬅️ Volver al Menú principal"):
        st.session_state.menu = "inicio"
        st.rerun()

    tab1, tab2 = st.tabs(["Descarga Individual", "Descarga Masiva (Excel)"])

    df_inventario = pd.DataFrame(hoja.get_all_records())
    if not df_inventario.empty:
        df_inventario['nombre'] = df_inventario['nombre'].astype(str).str.strip()
        df_inventario['lote'] = df_inventario['lote'].astype(str).str.strip()
        df_inventario['vencimiento'] = df_inventario['vencimiento'].astype(str).str.strip()
        df_con_stock = df_inventario[df_inventario['cantidad'] > 0]
    else:
        df_con_stock = pd.DataFrame()

    # --- TAB 1: INDIVIDUAL ---
    with tab1:
        st.markdown("### Complete los datos del retiro")
        st.write("---")
        
        if df_con_stock.empty:
            st.warning("⚠️ No hay medicamentos con stock disponible.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                nombres_unicos = sorted(df_con_stock['nombre'].unique())
                med_seleccionado = st.selectbox("1️⃣ Buscar Medicamento", options=["Seleccione..."] + nombres_unicos)
                
                opciones_lote = ["Seleccione..."]
                if med_seleccionado != "Seleccione...":
                    df_filtrado_nombre = df_con_stock[df_con_stock['nombre'] == med_seleccionado]
                    opciones_lote = ["Seleccione..."] + sorted(df_filtrado_nombre['lote'].unique())
                    
                lote_seleccionado = st.selectbox("2️⃣ Seleccionar Lote", options=opciones_lote)

            with col2:
                opciones_venc = ["Seleccione..."]
                stock_maximo = 100 
                indice_real = None

                if lote_seleccionado != "Seleccione...":
                    df_filtrado_lote = df_con_stock[(df_con_stock['nombre'] == med_seleccionado) & (df_con_stock['lote'] == lote_seleccionado)]
                    venc_unicos = sorted(df_filtrado_lote['vencimiento'].unique())
                    opciones_venc = venc_unicos if len(venc_unicos) == 1 else ["Seleccione..."] + venc_unicos
                        
                venc_seleccionado = st.selectbox("3️⃣ Fecha de Vencimiento", options=opciones_venc)
                
                if venc_seleccionado != "Seleccione...":
                    fila_exacta = df_con_stock[(df_con_stock['nombre'] == med_seleccionado) & (df_con_stock['lote'] == lote_seleccionado) & (df_con_stock['vencimiento'] == venc_seleccionado)]
                    if not fila_exacta.empty:
                        stock_maximo = int(fila_exacta.iloc[0]['cantidad'])
                        indice_real = fila_exacta.index[0]
                        st.info(f"📦 Stock disponible: **{stock_maximo}** unidades")

                tope_input = stock_maximo if venc_seleccionado != "Seleccione..." else 100
                cantidad_a_retirar = st.number_input("4️⃣ Cantidad a retirar", min_value=1, max_value=tope_input, step=1)

            st.write("#")
            btn_confirmar = st.button("✅ Confirmar Descarga", type="primary", use_container_width=True)

            if btn_confirmar:
                if "Seleccione..." in [med_seleccionado, lote_seleccionado, venc_seleccionado]:
                    st.error("⚠️ Faltó seleccionar algún dato.")
                elif cantidad_a_retirar > stock_maximo:
                    st.error(f"❌ Solo hay {stock_maximo} unidades disponibles.")
                else:
                    fila_google = int(indice_real) + 2
                    nuevo_stock = stock_maximo - cantidad_a_retirar
                    hoja.update_cell(fila_google, 4, nuevo_stock)
                    st.success(f"🎉 Retiraste {cantidad_a_retirar} de {med_seleccionado}. Stock actualizado.")

    # --- TAB 2: MASIVA ---
    with tab2:
        st.markdown("### 📥 Procesar Planilla de Pedidos (Excel)")
        st.info("Sube tu archivo 'PLANILLA DE RELEVAMIENTO DE PEDIDOS'. El sistema leerá automáticamente a partir de la fila 3.")
        
        archivo_descarga = st.file_uploader("Selecciona la Planilla de Excel", type=["xlsx", "xls"], key="descarga_masiva")
        
        if archivo_descarga is not None and not df_con_stock.empty:
            try:
                # LA MAGIA ESTÁ AQUÍ: header=1 le dice a Python que ignore la fila 1 del logo y use la fila 2 como títulos.
                df_excel_descarga = pd.read_excel(archivo_descarga, header=1)
                
                # Limpiamos las filas vacías que puedan quedar al final del excel
                col_medicamento = df_excel_descarga.columns[1] # Toma la columna B
                df_excel_descarga = df_excel_descarga.dropna(subset=[col_medicamento])

                st.write("---")
                todo_listo = True
                operaciones_a_realizar = []

                # Iteramos por los datos reales
                for i, fila_excel in df_excel_descarga.iterrows():
                    med_req = str(fila_excel.iloc[1]).strip() # Columna B (Medicamento)
                    
                    # Intentamos leer la cantidad, si está vacía o es un texto, la saltamos
                    try:
                        cant_req = int(fila_excel.iloc[2]) # Columna C (Entrega)
                    except ValueError:
                        continue 
                        
                    if cant_req <= 0:
                        continue
                        
                    st.markdown(f"📦 **{med_req}** | Necesitas retirar: **{cant_req}** unid.")
                    
                    df_filtrado = df_con_stock[df_con_stock['nombre'] == med_req]
                    
                    if df_filtrado.empty:
                        st.error(f"❌ No tienes stock de {med_req} en tu inventario.")
                        todo_listo = False
                    else:
                        col_lote, col_venc, col_status = st.columns(3)
                        
                        with col_lote:
                            lotes_disp = sorted(df_filtrado['lote'].unique())
                            lote_sel = st.selectbox("Lote", options=["Seleccione..."] + lotes_disp, key=f"lote_desc_{i}")
                            
                        with col_venc:
                            venc_sel = "Seleccione..."
                            if lote_sel != "Seleccione...":
                                df_lote = df_filtrado[df_filtrado['lote'] == lote_sel]
                                venc_disp = sorted(df_lote['vencimiento'].unique())
                                if len(venc_disp) == 1:
                                    venc_sel = venc_disp[0]
                                    st.info(venc_sel)
                                else:
                                    venc_sel = st.selectbox("Vencimiento", options=["Seleccione..."] + venc_disp, key=f"venc_desc_{i}")
                                    
                        with col_status:
                            if lote_sel != "Seleccione..." and venc_sel != "Seleccione...":
                                fila_exacta = df_filtrado[(df_filtrado['lote'] == lote_sel) & (df_filtrado['vencimiento'] == venc_sel)]
                                if not fila_exacta.empty:
                                    stock_real = int(fila_exacta.iloc[0]['cantidad'])
                                    idx_real = fila_exacta.index[0]
                                    
                                    if cant_req > stock_real:
                                        st.error(f"❌ Faltan unidades. Solo hay {stock_real}.")
                                        todo_listo = False
                                    else:
                                        st.success(f"✅ OK (Quedarán {stock_real - cant_req})")
                                        operaciones_a_realizar.append({
                                            'indice_excel_nube': int(idx_real) + 2,
                                            'nuevo_stock': stock_real - cant_req,
                                            'nombre': med_req
                                        })
                            else:
                                st.warning("⚠️ Elige lote y fecha")
                                todo_listo = False
                    st.write("---")

                if todo_listo and len(operaciones_a_realizar) > 0:
                    if st.button("🚀 Confirmar Todas las Descargas", type="primary", use_container_width=True):
                        for op in operaciones_a_realizar:
                            hoja.update_cell(op['indice_excel_nube'], 4, op['nuevo_stock'])
                        st.success(f"🎉 ¡Éxito! Base de datos actualizada con los retiros.")
                        st.rerun()

            except Exception as e:
                st.error(f"❌ Error al leer la planilla. Detalle técnico: {e}")

# ==========================================
# --- PANTALLA STOCK ---
# ==========================================
elif st.session_state.menu == "stock":
    st.markdown("<style>.block-container { padding-top: 2rem; }</style>", unsafe_allow_html=True)
    st.title("📋 Stock de Farmacia")
    if st.button("⬅️ Volver al Menú principal"):
        st.session_state.menu = "inicio"
        st.rerun()
    st.info("Próximamente: Tabla de stock.")