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
    """Calcula ganancias SOLO para escenarios REALES"""
    com_factor = 1 - commission
    
    # ESCENARIOS REALES (solo 1ro y 2do lugar como colocado)
    G1 = a*(win1-1) - b - x*(place1-1) + y*com_factor  # G1 gana, G2 no coloca
    G2 = -a + b*(win2-1) + x*com_factor - y*(place2-1)  # G2 gana, G1 no coloca
    G3 = -a + b*(win2-1) - x*(place1-1) - y*(place2-1)  # G1 2do, G2 gana
    G4 = a*(win1-1) - b - x*(place1-1) - y*(place2-1)   # G2 2do, G1 gana
    G5 = -a - b + x*com_factor + y*com_factor           # Ambos no colocan
    
    # ESCENARIOS CON OTRO GANADOR (solo 2do lugar como colocado)
    G6 = -a - b - x*(place1-1) + y*com_factor           # Otro gana, G1 2do, G2 no coloca
    G7 = -a - b + x*com_factor - y*(place2-1)           # Otro gana, G2 2do, G1 no coloca
    G8 = -a - b - x*(place1-1) - y*(place2-1)           # Otro gana, G1 y G2 2do y 3ro (AMBOS COLOCAN) - ¡ESTO SÍ EXISTE!
    
    return [G1, G2, G3, G4, G5, G6, G7, G8]

def optimizacion_minimizar_perdidas(win1, win2, place1, place2, commission=0.02):
    """Optimización ESPECÍFICA para MINIMIZAR PÉRDIDAS"""
    a, b = calcular_stakes_ganador(win1, win2)
    
    # Calcular probabilidades para guess inicial
    prob_place1 = 1 / place1
    prob_place2 = 1 / place2
    
    # GUESS INICIAL CONSERVADOR - priorizar reducir pérdidas máximas
    if prob_place1 > prob_place2:
        guess_x = min(prob_place1 * 2.0, 1.5)  # Más conservador
        guess_y = max(prob_place2 * 0.8, 0.4)   # Más conservador
    else:
        guess_x = max(prob_place1 * 0.8, 0.4)
        guess_y = min(prob_place2 * 2.0, 1.5)
    
    best_x, best_y = guess_x, guess_y
    best_perdida_max = float('inf')
    best_ganancia_min = -float('inf')
    
    # BÚSQUEDA ESPECÍFICA PARA MINIMIZAR PÉRDIDAS
    for x in np.arange(0.3, 2.5, 0.05):
        for y in np.arange(0.3, 2.5, 0.05):
            ganancias = calcular_ganancias_reales(a, b, x, y, win1, win2, place1, place2, commission)
            
            perdida_max = min(ganancias)  # Lo que queremos minimizar
            ganancia_min = min([g for g in ganancias if g >= 0] or [0])  # Mínima ganancia positiva
            
            # CRITERIO PRINCIPAL: minimizar pérdida máxima
            # CRITERIO SECUNDARIO: maximizar ganancia mínima positiva
            if perdida_max > best_perdida_max or (abs(perdida_max - best_perdida_max) < 0.01 and ganancia_min > best_ganancia_min):
                best_perdida_max = perdida_max
                best_ganancia_min = ganancia_min
                best_x, best_y = x, y
    
    return a, b, best_x, best_y

# INTERFAZ STREAMLIT ESPECIALIZADA
st.set_page_config(page_title="Minimizador de Pérdidas", page_icon="🛡️", layout="centered")

st.title("🛡️ Optimizador para MINIMIZAR PÉRDIDAS")

st.info("🎯 **Estrategia conservadora** - Prioriza reducir pérdidas máximas sobre maximizar ganancias")

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

# Calcular estrategia MINIMIZANDO PÉRDIDAS
if st.button("🛡️ Calcular Estrategia Conservadora"):
    with st.spinner("Buscando stakes que minimicen pérdidas..."):
        stake_win1, stake_win2, stake_lay1, stake_lay2 = optimizacion_minimizar_perdidas(
            win1, win2, place1, place2, commission
        )
        ganancias = calcular_ganancias_reales(
            stake_win1, stake_win2, stake_lay1, stake_lay2,
            win1, win2, place1, place2, commission
        )
    
    # MOSTRAR RESULTADOS FOCALIZADOS EN PÉRDIDAS
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
        ganancia_min = min([g for g in ganancias if g >= 0] or [0])
        st.metric("Pérdida Máxima", f"${perdida_max:.3f}")
        st.metric("Ganancia Mínima", f"${ganancia_min:.3f}")
    
    # TABLA DE ESCENARIOS CON FOCO EN PÉRDIDAS
    st.subheader("📈 Escenarios Reales - Análisis de Pérdidas")
    
    escenarios_reales = [
        "G1 gana, G2 no coloca",
        "G2 gana, G1 no coloca", 
        "G1 2do, G2 gana",
        "G2 2do, G1 gana",
        "Ambos no colocan",
        "OTRO gana, G1 2do, G2 no coloca",
        "OTRO gana, G2 2do, G1 no coloca", 
        "OTRO gana, AMBOS 2do y 3ro"
    ]
    
    resultados = []
    for i, (esc, gan) in enumerate(zip(escenarios_reales, ganancias)):
        # Destacar escenarios con pérdida
        if gan < 0:
            estilo = "🔴" 
        elif gan < 0.5:
            estilo = "🟡"
        else:
            estilo = "🟢"
            
        resultados.append({
            'Escenario': f"{estilo} {esc}",
            'Ganancia/Neta': f"${gan:.3f}",
            'Tipo': "PÉRDIDA" if gan < 0 else "ganancia baja" if gan < 0.5 else "ganancia buena"
        })
    
    st.table(pd.DataFrame(resultados))
    
    # ANÁLISIS DE RIESGO DETALLADO
    st.subheader("📊 Análisis de Riesgo Detallado")
    
    perdidas = [g for g in ganancias if g < 0]
    ganancias_positivas = [g for g in ganancias if g >= 0]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Escenarios con Pérdida", f"{len(perdidas)}/{len(ganancias)}")
        if perdidas:
            st.metric("Pérdida Promedio", f"${np.mean(perdidas):.3f}")
    
    with col2:
        st.metric("Escenarios con Ganancia", f"{len(ganancias_positivas)}/{len(ganancias)}")
        if ganancias_positivas:
            st.metric("Ganancia Promedio", f"${np.mean(ganancias_positivas):.3f}")
    
    with col3:
        ratio_riesgo = abs(min(ganancias)) / max(ganancias) if max(ganancias) > 0 else 0
        st.metric("Ratio Riesgo/Beneficio", f"{ratio_riesgo:.2f}:1")
    
    # RECOMENDACIÓN BASADA EN RIESGO
    st.subheader("💡 Recomendación de Estrategia")
    
    if len(perdidas) <= 2 and min(ganancias) > -1.0:
        st.success("**✅ ESTRATEGIA ACEPTABLE** - Pérdidas controladas y riesgo limitado")
    elif len(perdidas) <= 3 and min(ganancias) > -2.0:
        st.warning("**⚠️ ESTRATEGIA MODERADA** - Algunas pérdidas significativas")
    else:
        st.error("**🔴 ESTRATEGIA RIESGOSA** - Considera ajustar las odds o no apostar")

st.markdown("---")
st.caption("⚠️ Herramienta educativa - Apueste responsablemente")
