import streamlit as st
import json
import os
from datetime import datetime

if not os.path.exists("datos"):
    os.makedirs("datos")

ARCHIVO_DATOS = "datos/registro_cajones.json"

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r") as f:
            return json.load(f)
    return []

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, "w") as f:
        json.dump(datos, f, indent=4)

st.title("Registro de Cajones y Quincena")

# 1. FORMULARIO DE CARGA
st.subheader("Cargar día de trabajo")
with st.form("carga_diaria", clear_on_submit=True):
    fecha = st.date_input("Fecha")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Cajones Comunes**")
        cajones_normal = st.number_input("Cantidad comunes", min_value=0, step=1)
        precio_normal = st.number_input("Precio común ($)", min_value=0.0, value=230.0, step=10.0)
    
    with col2:
        st.markdown("**Jaulas Grandes (JG)**")
        cajones_jg = st.number_input("Cantidad JG", min_value=0, step=1)
        precio_jg = st.number_input("Precio JG ($)", min_value=0.0, value=250.0, step=10.0)
    
    submit = st.form_submit_button("Guardar Día")
    
    if submit:
        if cajones_normal == 0 and cajones_jg == 0:
            st.warning("No cargaste ningún cajón. Revisa los números.")
        else:
            datos = cargar_datos()
            plata_normales = cajones_normal * precio_normal
            plata_jg = cajones_jg * precio_jg
            ganancia_dia = plata_normales + plata_jg
            total_cajones = cajones_normal + cajones_jg
            
            nuevo_registro = {
                "fecha": str(fecha),
                "comunes": cajones_normal,
                "precio_comun": precio_normal,
                "jg": cajones_jg,
                "precio_jg": precio_jg,
                "total_cajones_dia": total_cajones,
                "ganancia_dia": ganancia_dia
            }
            datos.append(nuevo_registro)
            guardar_datos(datos)
            st.success(f"Día guardado: ganancia de ${ganancia_dia:,.2f}")
            # st.rerun() recarga la página para mostrar los datos actualizados al instante
            st.rerun()

st.divider()

# 2. RESUMEN DE LA QUINCENA CON FILTROS
st.subheader("Liquidación")
datos = cargar_datos()

if datos:
    opcion_quincena = st.radio(
        "Selecciona el período a calcular:",
        ["Primera Quincena (1 al 15)", "Segunda Quincena (16 al 31)", "Todo el historial"],
        horizontal=True
    )
    
    datos_filtrados = []
    for d in datos:
        dia_registro = datetime.strptime(d["fecha"], "%Y-%m-%d").day
        if opcion_quincena == "Primera Quincena (1 al 15)" and dia_registro <= 15:
            datos_filtrados.append(d)
        elif opcion_quincena == "Segunda Quincena (16 al 31)" and dia_registro >= 16:
            datos_filtrados.append(d)
        elif opcion_quincena == "Todo el historial":
            datos_filtrados.append(d)

    if datos_filtrados:
        total_comunes = sum(d.get("comunes", d.get("normales", 0)) for d in datos_filtrados)
        total_jg = sum(d.get("jg", 0) for d in datos_filtrados)
        plata_total = sum(d["ganancia_dia"] for d in datos_filtrados)
        
        col3, col4, col5 = st.columns(3)
        col3.metric("Comunes en este período", total_comunes)
        col4.metric("JG en este período", total_jg)
        col5.metric("Plata de la Quincena", f"${plata_total:,.2f}")
        
        st.dataframe(datos_filtrados)
    else:
        st.info("No hay registros guardados para esta quincena.")

    st.divider()
    
    # 3. ZONA PARA BORRAR REGISTROS (NUEVO)
    st.subheader("Corregir errores")
    # Creamos una lista de opciones para que elijas qué día borrar
    opciones_borrar = [f"{i} - Fecha: {d['fecha']} | Comunes: {d.get('comunes',0)} | JG: {d.get('jg',0)}" for i, d in enumerate(datos)]
    
    registro_a_borrar = st.selectbox("Selecciona un registro si necesitas eliminarlo:", opciones_borrar)
    
    if st.button("Eliminar Registro"):
        # Extraemos el índice (el número) de la opción elegida
        indice = int(registro_a_borrar.split(" - ")[0])
        datos.pop(indice) # Borramos ese elemento de la lista
        guardar_datos(datos) # Guardamos el archivo actualizado
        st.success("Registro eliminado.")
        st.rerun()

else:
    st.info("Aún no hay días registrados en el sistema.")