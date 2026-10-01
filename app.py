import streamlit as st
import json
from datetime import datetime
import gspread

# 1. Configurar la conexión a Google Sheets
@st.cache_resource
def conectar_gsheets():
    # Lee la llave secreta que pusimos en Streamlit Cloud
    creds_dict = json.loads(st.secrets["gcp_credentials"])
    gc = gspread.service_account_from_dict(creds_dict)
    # Abre tu planilla por su nombre (debe ser el mismo que pusiste en Google Drive)
    return gc.open("Registro_Cajones").sheet1

try:
    sheet = conectar_gsheets()
except Exception as e:
    st.error(f"Error conectando a Google Sheets. Revisa los permisos o el nombre de la planilla. Detalle: {e}")
    st.stop()

def cargar_datos():
    # Trae todas las filas de tu Excel
    return sheet.get_all_records()

st.title("Registro de Cajones y Quincena")

# 2. FORMULARIO DE CARGA
st.subheader("Cargar día de trabajo")
with st.form("carga_diaria", clear_on_submit=True):
    fecha = st.date_input("Fecha")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Cajones Comunes**")
        cajones_normal = st.number_input("Cantidad comunes", min_value=0, step=1)
        precio_normal = st.number_input("Precio común ($)", min_value=0.0, value=280.0, step=10.0)
    with col2:
        st.markdown("**Jaulas Grandes (JG)**")
        cajones_jg = st.number_input("Cantidad JG", min_value=0, step=1)
        precio_jg = st.number_input("Precio JG ($)", min_value=0.0, value=350.0, step=10.0)
    
    submit = st.form_submit_button("Guardar Día")
    
    if submit:
        if cajones_normal == 0 and cajones_jg == 0:
            st.warning("No cargaste ningún cajón.")
        else:
            plata_normales = cajones_normal * precio_normal
            plata_jg = cajones_jg * precio_jg
            ganancia_dia = plata_normales + plata_jg
            total_cajones = cajones_normal + cajones_jg
            
            # Ordenar los datos exactamente como las columnas de tu Google Sheet (A a G)
            nueva_fila = [
                str(fecha),
                cajones_normal,
                precio_normal,
                cajones_jg,
                precio_jg,
                total_cajones,
                ganancia_dia
            ]
            sheet.append_row(nueva_fila)
            st.success(f"Día guardado en la nube: ganancia de ${ganancia_dia:,.2f}")
            st.rerun()

st.divider()

# 3. RESUMEN DE LA QUINCENA
st.subheader("Liquidación (Desde la Nube)")
datos = cargar_datos()

if datos:
    opcion_quincena = st.radio(
        "Selecciona el período a calcular:",
        ["Todo el historial", "Primera Quincena (1 al 15)", "Segunda Quincena (16 al 31)"],
        horizontal=True
    )
    
    datos_filtrados = []
    for d in datos:
        dia_registro = datetime.strptime(str(d["fecha"]), "%Y-%m-%d").day
        if opcion_quincena == "Primera Quincena (1 al 15)" and dia_registro <= 15:
            datos_filtrados.append(d)
        elif opcion_quincena == "Segunda Quincena (16 al 31)" and dia_registro >= 16:
            datos_filtrados.append(d)
        elif opcion_quincena == "Todo el historial":
            datos_filtrados.append(d)

    if datos_filtrados:
        total_comunes = sum(d.get("comunes", 0) for d in datos_filtrados)
        total_jg = sum(d.get("jg", 0) for d in datos_filtrados)
        plata_total = sum(d.get("ganancia_dia", 0) for d in datos_filtrados)
        
        col3, col4, col5 = st.columns(3)
        col3.metric("Comunes", total_comunes)
        col4.metric("JG", total_jg)
        col5.metric("Plata de la Quincena", f"${plata_total:,.2f}")
        
        st.dataframe(datos_filtrados)
    else:
        st.info("No hay registros para este período.")

    st.divider()
    
    # 4. ZONA PARA BORRAR REGISTROS DE LA NUBE
    st.subheader("Corregir errores")
    opciones_borrar = [f"{i} - Fecha: {d['fecha']} | Comunes: {d.get('comunes',0)} | JG: {d.get('jg',0)}" for i, d in enumerate(datos)]
    
    registro_a_borrar = st.selectbox("Selecciona un registro si necesitas eliminarlo:", opciones_borrar)
    
    if st.button("Eliminar Registro de la Nube"):
        indice = int(registro_a_borrar.split(" - ")[0])
        # En Google Sheets la fila 1 son los títulos, así que sumamos 2 al índice
        fila_a_borrar = indice + 2 
        sheet.delete_rows(fila_a_borrar)
        st.success("Registro eliminado permanentemente de tu Excel.")
        st.rerun()
else:
    st.info("Aún no hay días registrados en la nube.")
