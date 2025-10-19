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

def calcular_ganancias_completas(a, b, x, y, win1, win2, place1, place2, commission=0.02):
    """Calcula ganancias para TODOS los escenarios"""
    com_factor = 1 - commission
    
    # Escenarios principales
    G1 = a*(win1-1) - b - x*(place1-1) + y*com_factor  # G1 gana, G2 no coloca
    G2 = -a + b*(win2-1) + x*com_factor - y*(place2-1)  # G2 gana, G1 no coloca
    G3 = -a + b*(win2-1) - x*(place1-1) - y*(place2-1)  # G1 2do, G2 gana
    G4 = a*(win1-1) - b - x*(place1-1) - y*(place2-1)   # G2 2do, G1 gana
    G5 = -a - b + x*com_factor + y*com_factor           # Ambos no colocan
    
    # Escenarios con otros galgos ganando
    G6 = -a - b + x*com_factor + y*com_factor           # Otro gana, ambos no colocan
    G7 = -a - b - x*(place1-1) + y*com_factor           # Otro gana, G1 coloca, G2 no
    G8 = -a - b + x*com_factor - y*(place2-1)           # Otro gana, G2 coloca, G1 no
    G9 = -a - b - x*(place1-1) - y*(place2-1)           # Otro gana, ambos colocan
    
    return [G1, G2, G3, G4, G5, G6, G7, G8, G9]

def optimizacion_robusta(win1, win2, place1, place2, commission=0.02):
    """Optimización ROBUSTA con búsqueda grid inteligente"""
    a, b = calcular_stakes_ganador(win1, win2)
    
    # CALCULAR PROBABILIDADES PARA GUESS INICIAL INTELIGENTE
    prob_win1 = 1 / win1
    prob_win2 = 1 / win2
    prob_place1 = 1 / place1
    prob_place2 = 1 / place2
    
    # GUESS INICIAL BASADO EN PROBABILIDADES
    if prob_place1 > prob_place2:
        # G1 más probable de colocar -> más stake Lay en G1
        guess_x = min(prob_place1 * 2.5, 2.0)
        guess_y = max(prob_place2 * 1.0, 0.3)
    else:
        # G2 más probable de colocar -> más stake Lay en G2
        guess_x = max(prob_place1 * 1.0, 0.3)
        guess_y = min(prob_place2 * 2.5, 2.0)
    
    best_x, best_y = guess_x, guess_y
    best_score = -float('inf')
    
    # BÚSQUEDA GRID INTELIGENTE alrededor del guess inicial
    for x in np.arange(max(0.2, guess_x - 0.8), min(3.0, guess_x + 0.8), 0.05):
        for y in np.arange(max(0.2, guess_y - 0.8), min(3.0, guess_y + 0.8), 0.05):
            ganancias = calcular_ganancias_completas(a, b, x, y, win1, win2, place1, place2, commission)
            
            # SCORE MEJORADO: considerar múltiples factores
            ganancia_min = min(ganancias)
            ganancia_promedio = np.mean(ganancias)
            escenarios_positivos = sum(1 for g in ganancias if g > 0)
            
            # Puntaje compuesto
            score = (ganancia_min * 0.6 + 
                    ganancia_promedio * 0.2 + 
                    escenarios_positivos * 0.2)
            
            if score > best_score:
                best_score = score
                best_x, best_y = x, y
    
    return a, b, best_x, best_y

# INTERFAZ STREAMLIT MEJORADA
st.set_page_config(page_title="Optimizador Robusto", page_icon="🏁", layout="centered")

st.title("🏁 Optimizador ROBUSTO con Búsqueda Inteligente")

st.info("🎯 **Optimización mejorada** - Guess inicial inteligente + búsqueda grid optimizada")

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
if st.button("🎲 Calcular con Optimización Robusta"):
    with st.spinner("Optimizando con búsqueda inteligente..."):
        stake_win1, stake_win2, stake_lay1, stake_lay2 = optimizacion_robusta(
            win1, win2, place1, place2, commission
        )
        ganancias = calcular_ganancias_completas(
            stake_win1, stake_win2, stake_lay1, stake_lay2,
            win1, win2, place1, place2, commission
        )
    
    # MOSTRAR RESULTADOS CON ANÁLISIS
    st.header("💡 Estrategia Optimizada - Resultados")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Back a Ganador")
        st.metric("Galgo 1", f"${stake_win1:.2f} @ {win1:.2f}")
        st.metric("Galgo 2", f"${stake_win2:.2f} @ {win2:.2f}")
    
    with col2:
        st.subheader("Lay a Colocado")
        st.metric("Contra Galgo 1", f"${stake_lay1:.2f}")
        st.metric("Contra Galgo 2", f"${stake_lay2:.2f}")
    
    with col3:
        st.subheader("📊 Análisis")
        prob_place1 = 1 / place1
        prob_place2 = 1 / place2
        st.write(f"Prob. G1 colocado: {prob_place1*100:.1f}%")
        st.write(f"Prob. G2 colocado: {prob_place2*100:.1f}%")
        st.write(f"Ratio Lay: {stake_lay1/stake_lay2:.2f}:1")
    
    # VERIFICACIÓN DE OPTIMIZACIÓN
    st.subheader("🔍 Verificación de la Optimización")
    
    # Probar stakes extremas para comparar
    test_stakes = [
        (0.1, 0.1, "Mínimas ($0.10 c/u)"),
        (1.0, 1.0, "Medias ($1.00 c/u)"), 
        (stake_lay1, stake_lay2, "OPTIMIZADAS"),
        (2.0, 2.0, "Máximas ($2.00 c/u)")
    ]
    
    comparacion = []
    for x, y, desc in test_stakes:
        g = calcular_ganancias_completas(stake_win1, stake_win2, x, y, win1, win2, place1, place2, commission)
        comparacion.append({
            'Stakes Lay': desc,
            'G1': f"${x:.2f}",
            'G2': f"${y:.2f}", 
            'Mínima': f"${min(g):.3f}",
            'Máxima': f"${max(g):.3f}",
            'Positivos': f"{sum(1 for v in g if v > 0)}/9"
        })
    
    st.table(pd.DataFrame(comparacion))
    
    # TABLA COMPLETA DE ESCENARIOS
    st.subheader("📈 Todos los Escenarios con Stakes Optimizadas")
    
    escenarios = [
        "G1 gana, G2 no coloca",
        "G2 gana, G1 no coloca", 
        "G1 2do, G2 gana",
        "G2 2do, G1 gana",
        "Ambos no colocan",
        "OTRO gana, ambos NO colocan",
        "OTRO gana, G1 COLOCA, G2 no", 
        "OTRO gana, G2 COLOCA, G1 no",
        "OTRO gana, AMBOS COLOCAN"
    ]
    
    resultados = []
    for i, (esc, gan) in enumerate(zip(escenarios, ganancias)):
        resultados.append({
            'Escenario': esc,
            'Ganancia/Neta': f"${gan:.3f}",
            'Resultado': "✅ Ganancia" if gan >= 0 else "⚠️ Pérdida"
        })
    
    st.table(pd.DataFrame(resultados))

# DEBUG: Mostrar guess inicial
with st.expander("🔧 Debug - Guess Inicial"):
    if 'win1' in locals():
        prob_p1 = 1 / place1
        prob_p2 = 1 / place2
        st.write(f"Prob. G1 colocado: {prob_p1:.3f} -> Guess Lay: {prob_p1 * 2.5:.2f}")
        st.write(f"Prob. G2 colocado: {prob_p2:.3f} -> Guess Lay: {prob_p2 * 2.5:.2f}")

st.markdown("---")
st.caption("⚠️ Herramienta educativa - Apueste responsablemente")
