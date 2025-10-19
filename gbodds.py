import streamlit as st
import pandas as pd
import numpy as np

def calcular_stakes_ganador(win1, win2, presupuesto_total=2.0):
    """Prorratea los stakes a ganador según las odds"""
    if abs(win1 - win2) < 0.01:
        return presupuesto_total / 2, presupuesto_total / 2
    else:
        inv1 = 1 / win1
        inv2 = 1 / win2
        total_inv = inv1 + inv2
        stake1 = (inv1 / total_inv) * presupuesto_total
        stake2 = (inv2 / total_inv) * presupuesto_total
        return stake1, stake2

def calcular_ganancias_reales(a, b, x, y, win1, win2, place1, place2, commission=0.02):
    """Calcula ganancias SOLO para escenarios REALES de colocado (1ro y 2do)"""
    com_factor = 1 - commission
    
    # ESCENARIOS REALES - COLOCADO = 1ro O 2do lugar
    G1 = a*(win1-1) - b - x*(place1-1) + y*com_factor  # G1 gana, G2 no coloca
    G2 = -a + b*(win2-1) + x*com_factor - y*(place2-1)  # G2 gana, G1 no coloca
    G3 = -a + b*(win2-1) - x*(place1-1) - y*(place2-1)  # G1 2do, G2 gana
    G4 = a*(win1-1) - b - x*(place1-1) - y*(place2-1)   # G2 2do, G1 gana
    G5 = -a - b + x*com_factor + y*com_factor           # Ambos no colocan
    
    # ESCENARIOS CON OTRO GANADOR - solo 2do lugar cuenta como colocado
    G6 = -a - b - x*(place1-1) + y*com_factor           # Otro gana, G1 2do, G2 no coloca
    G7 = -a - b + x*com_factor - y*(place2-1)           # Otro gana, G2 2do, G1 no coloca
    
    # ¡NO EXISTE "Otro gana, ambos colocan" porque solo hay 2 puestos de colocado!
    
    return [G1, G2, G3, G4, G5, G6, G7]

def optimizacion_minimizar_perdidas(win1, win2, place1, place2, commission=0.02):
    """Optimización ESPECÍFICA para MINIMIZAR PÉRDIDAS"""
    a, b = calcular_stakes_ganador(win1, win2)
    
    # Calcular probabilidades para guess inicial
    prob_place1 = 1 / place1
    prob_place2 = 1 / place2
    
    # GUESS INICIAL CONSERVADOR
    if prob_place1 > prob_place2:
        guess_x = min(prob_place1 * 2.0, 1.5)
        guess_y = max(prob_place2 * 0.8, 0.4)
    else:
        guess_x = max(prob_place1 * 0.8, 0.4)
        guess_y = min(prob_place2 * 2.0, 1.5)
    
    best_x, best_y = guess_x, guess_y
    best_perdida_max = float('inf')
    
    # BÚSQUEDA PARA MINIMIZAR PÉRDIDA MÁXIMA
    for x in np.arange(0.3, 2.5, 0.05):
        for y in np.arange(0.3, 2.5, 0.05):
            ganancias = calcular_ganancias_reales(a, b, x, y, win1, win2, place1, place2, commission)
            
            perdida_max = min(ganancias)  # Lo que queremos minimizar
            
            # CRITERIO: minimizar pérdida máxima
            if perdida_max > best_perdida_max:
                best_perdida_max = perdida_max
                best_x, best_y = x, y
    
    return a, b, best_x, best_y

# INTERFAZ STREAMLIT
st.set_page_config(page_title="Minimizador de Pérdidas", page_icon="🛡️", layout="centered")

st.title("🛡️ Optimizador para MINIMIZAR PÉRDIDAS")

st.info("🎯 **Solo escenarios REALES** - Colocado = 1ro o 2do lugar")

with st.sidebar:
    st.header("⚙️ Configuración")
    
    st.subheader("Odds de los Galgos")
    col1, col2 = st.columns(2)
    
    with col1:
        win1 = st.number_input("G1 - Ganar", value=4.2, min_value=1.0, key="win1")
        place1 = st.number_input("G1 - Colocado", value=2.2, min_value=1.0, key="place1")
    
    with col2:
        win2 = st.number_input("G2 - Ganar", value=5.2, min_value=1.0, key="win2")  
        place2 = st.number_input("G2 - Colocado", value=2.2, min_value=1.0, key="place2")
    
    presupuesto = st.number_input("💰 Presupuesto Back ($)", value=2.0, min_value=1.0, step=0.5)
    commission = st.slider("🎯 Comisión Exchange (%)", 0.0, 10.0, 2.0) / 100

# Calcular estrategia
if st.button("🛡️ Calcular Estrategia Conservadora"):
    with st.spinner("Buscando stakes que minimicen pérdidas..."):
        stake_win1, stake_win2, stake_lay1, stake_lay2 = optimizacion_minimizar_perdidas(
            win1, win2, place1, place2, commission
        )
        ganancias = calcular_ganancias_reales(
            stake_win1, stake_win2, stake_lay1, stake_lay2,
            win1, win2, place1, place2, commission
        )
    
    # MOSTRAR RESULTADOS
    st.header("💡 Estrategia para Minimizar Pérdidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Back a Ganador")
        st.metric("Galgo 1", f"${stake_win1:.2f}")
        st.metric("Galgo 2", f"${stake_win2:.2f}")
    
    with col2:
        st.subheader("Lay a Colocado")
        st.metric("Contra Galgo 1", f"${stake_lay1:.2f}")
        st.metric("Contra Galgo 2", f"${stake_lay2:.2f}")
    
    with col3:
        st.subheader("🛡️ Protección")
        perdida_max = min(ganancias)
        st.metric("Pérdida Máxima", f"${perdida_max:.3f}")
        st.metric("Escenarios Total", f"{len(ganancias)}")
    
    # TABLA DE ESCENARIOS REALES
    st.subheader("📈 Escenarios REALES de Colocado (1ro y 2do)")
    
    escenarios_reales = [
        "G1 gana, G2 no coloca",
        "G2 gana, G1 no coloca", 
        "G1 2do, G2 gana",
        "G2 2do, G1 gana",
        "Ambos no colocan",
        "OTRO gana, G1 2do, G2 no coloca",
        "OTRO gana, G2 2do, G1 no coloca"
        # ¡NO EXISTE "Otro gana, ambos colocan"!
    ]
    
    resultados = []
    for i, (esc, gan) in enumerate(zip(escenarios_reales, ganancias)):
        resultados.append({
            'Escenario': esc,
            'Ganancia/Neta': f"${gan:.3f}",
            'Resultado': "✅ Ganancia" if gan >= 0 else "⚠️ Pérdida"
        })
    
    st.table(pd.DataFrame(resultados))
    
    # ANÁLISIS DE RIESGO
    st.subheader("📊 Análisis de Riesgo Real")
    
    perdidas = [g for g in ganancias if g < 0]
    ganancias_positivas = [g for g in ganancias if g >= 0]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Escenarios con Pérdida", f"{len(perdidas)}/{len(ganancias)}")
    
    with col2:
        st.metric("Escenarios con Ganancia", f"{len(ganancias_positivas)}/{len(ganancias)}")
    
    with col3:
        if ganancias_positivas:
            ratio = abs(min(ganancias)) / max(ganancias_positivas) if max(ganancias_positivas) > 0 else 0
            st.metric("Ratio Riesgo/Beneficio", f"{ratio:.2f}:1")
    
    # EXPLICACIÓN DE ESCENARIOS
    with st.expander("🔍 Explicación de Escenarios Reales"):
        st.write("""
        **Colocado = 1ro O 2do lugar (solo 2 puestos)**
        
        - **G1 gana, G2 no coloca**: G1 es 1ro, G2 es 3ro-6to
        - **G2 gana, G1 no coloca**: G2 es 1ro, G1 es 3ro-6to  
        - **G1 2do, G2 gana**: G2 es 1ro, G1 es 2do
        - **G2 2do, G1 gana**: G1 es 1ro, G2 es 2do
        - **Ambos no colocan**: G1 y G2 son 3ro-6to
        - **OTRO gana, G1 2do, G2 no coloca**: Otro galgo es 1ro, G1 es 2do, G2 es 3ro-6to
        - **OTRO gana, G2 2do, G1 no coloca**: Otro galgo es 1ro, G2 es 2do, G1 es 3ro-6to
        
        **❌ NO EXISTE**: "Otro gana, ambos colocan" porque solo hay 2 puestos de colocado
        """)

st.markdown("---")
st.caption("⚠️ Herramienta educativa - Apueste responsablemente")
