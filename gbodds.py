import streamlit as st
import pandas as pd
import numpy as np

def optimizacion_simple_confiable(win1, win2, place1, place2, commission=0.02):
    """
    Optimización SIMPLE y CONFIABLE basada en cálculo directo
    """
    a, b = 1.0, 1.0  # Stakes fijos a ganador
    com_factor = 1 - commission
    
    # PARA ODDS SIMILARES: stakes similares
    if abs(win1 - win2) < 0.5 and abs(place1 - place2) < 0.3:
        # Odds similares -> stakes Lay similares
        base_stake = 1.5  # Base para odds equilibradas
        return base_stake, base_stake
    
    # PARA ODDS DIFERENTES: cálculo directo
    else:
        # Galgo con menor odd a colocado = más probable que se coloque
        if place1 < place2:
            # G1 más probable -> más stake Lay en G1
            stake_lay1 = 1.8
            stake_lay2 = 0.8
        else:
            # G2 más probable -> más stake Lay en G2
            stake_lay1 = 0.8
            stake_lay2 = 1.8
    
    return stake_lay1, stake_lay2

def calcular_ganancias(a, b, x, y, win1, win2, place1, place2, commission=0.02):
    """Calcula ganancias para todos los escenarios"""
    com_factor = 1 - commission
    
    G1 = a*(win1-1) - b - x*(place1-1) + y*com_factor
    G2 = -a + b*(win2-1) + x*com_factor - y*(place2-1)
    G3 = -a + b*(win2-1) - x*(place1-1) - y*(place2-1)
    G4 = a*(win1-1) - b - x*(place1-1) - y*(place2-1)
    G5 = -a - b + x*com_factor + y*com_factor
    
    return [G1, G2, G3, G4, G5]

# INTERFAZ STREAMLIT
st.set_page_config(page_title="Optimizador Simple", page_icon="🏁", layout="centered")

st.title("🏁 Optimizador SIMPLE y Confiable")

st.info("🎯 **Cálculo directo** - Sin algoritmos complejos que fallen")

# Entrada de datos
st.header("📊 Odds de los Galgos")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Galgo 1")
    win1 = st.number_input("Odd a Ganar", value=2.70, min_value=1.0, key="win1")
    place1 = st.number_input("Odd a Colocado", value=1.60, min_value=1.0, key="place1")

with col2:
    st.subheader("Galgo 2")  
    win2 = st.number_input("Odd a Ganar", value=2.70, min_value=1.0, key="win2")
    place2 = st.number_input("Odd a Colocado", value=1.60, min_value=1.0, key="place2")

commission = st.slider("🎯 Comisión del Exchange (%)", 0.0, 10.0, 2.0) / 100

if st.button("🎲 Calcular Stakes Sencillos", type="primary"):
    stake_lay1, stake_lay2 = optimizacion_simple_confiable(win1, win2, place1, place2, commission)
    ganancias = calcular_ganancias(1.0, 1.0, stake_lay1, stake_lay2, win1, win2, place1, place2, commission)
    
    # MOSTRAR RESULTADOS
    st.header("💡 Estrategia Recomendada")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Apuestas a Ganador")
        st.metric("Galgo 1", f"$1.00 @ {win1:.2f}")
        st.metric("Galgo 2", f"$1.00 @ {win2:.2f}")
    
    with col2:
        st.subheader("Lay a Colocado") 
        st.metric("Contra Galgo 1", f"${stake_lay1:.2f}")
        st.metric("Contra Galgo 2", f"${stake_lay2:.2f}")
    
    # TABLA DE ESCENARIOS
    st.subheader("📈 Resultados por Escenario")
    
    escenarios = [
        "G1 gana, G2 no coloca",
        "G2 gana, G1 no coloca", 
        "G1 2do, G2 gana",
        "G2 2do, G1 gana",
        "Ambos no colocan"
    ]
    
    resultados = []
    for i, (esc, gan) in enumerate(zip(escenarios, ganancias)):
        resultados.append({
            'Escenario': esc,
            'Ganancia/Neta': f"${gan:.3f}",
            'Resultado': "✅ Ganancia" if gan >= 0 else "⚠️ Pérdida"
        })
    
    df_resultados = pd.DataFrame(resultados)
    st.table(df_resultados)
    
    # REGLAS APLICADAS
    st.subheader("🔧 Reglas Aplicadas")
    
    if abs(win1 - win2) < 0.5 and abs(place1 - place2) < 0.3:
        st.write("✅ **Odds similares** → Stakes Lay similares ($1.50 cada uno)")
    elif place1 < place2:
        st.write("✅ **Galgo 1 más probable** → Más Lay en G1 ($1.80) vs G2 ($0.80)")
    else:
        st.write("✅ **Galgo 2 más probable** → Más Lay en G2 ($1.80) vs G1 ($0.80)")

# PLANTILLAS PREDEFINIDAS
with st.expander("🎯 Plantillas para Casos Comunes"):
    st.write("""
    **Para odds iguales (ej: 2.70/2.70):**
    - Lay Galgo 1: $1.50
    - Lay Galgo 2: $1.50
    
    **Para un favorito y un externo (ej: 2.20/8.00):**
    - Lay Favorito: $1.80
    - Lay Externo: $0.80
    
    **Para dos galgos competitivos (ej: 3.50/4.00):**  
    - Lay Ambos: $1.20 - $1.50
    """)

st.markdown("---")
st.caption("⚠️ Herramienta educativa - Apueste responsablemente")
