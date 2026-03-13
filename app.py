import streamlit as st

# 1. Configuración y Estilo CSS para que se parezca a tu imagen
st.set_page_config(page_title="Farmacia Hospital", layout="wide")

st.markdown("""
    <style>
    .main {
        background-color: #333333; /* Color de fondo oscuro como tu imagen */
    }
    div.stButton > button {
        background-color: #E0E0E0; /* Gris claro de las tarjetas */
        color: #000000;
        height: 150px;
        width: 100%;
        border-radius: 20px; /* Bordes redondeados */
        border: none;
        font-size: 20px;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #CCCCCC;
        transform: scale(1.05); /* Efecto de aumento al pasar el mouse */
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Inicializar el estado de navegación
if 'menu' not in st.session_state:
    st.session_state.menu = "inicio"

# 3. Función para cambiar de pantalla
def cambiar_pantalla(nombre):
    st.session_state.menu = nombre

# --- LÓGICA DE PANTALLAS ---

if st.session_state.menu == "inicio":
    st.write("#") # Espaciado
    st.write("#")
    
    # Creamos 3 columnas para que queden centrados y en línea como tu diseño
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("CARGA\n\n+"):
            cambiar_pantalla("carga")
            st.rerun()

    with col2:
        if st.button("STOCK\n\n="):
            cambiar_pantalla("stock")
            st.rerun()

    with col3:
        if st.button("DESCARGA\n\n-"):
            cambiar_pantalla("descarga")
            st.rerun()

elif st.session_state.menu == "carga":
    if st.button("⬅️ Volver al Menú"):
        cambiar_pantalla("inicio")
        st.rerun()
    st.subheader("📝 Formulario de Carga de Medicamentos")
    # Aquí iría el código de Google Sheets que ya teníamos
    
# (Y así con el resto de las pantallas...)