import streamlit as st
import pandas as pd
import numpy as np

def calcular_stakes_ganador(win1, win2, presupuesto_total=2.0):
    """Prorratea los stakes a ganador según las odds"""
    if abs(win1 - win2) < 0.01:
        stake1 = presupuesto_total / 2
        stake2 = presupuesto_total / 2
    else:
        inv1 = 1 / win1
        inv2 = 1 / win2
        total_inv = inv1 + inv2
        stake1 = (inv1 / total_inv) * presupuesto_total
        stake2 = (inv2 / total_inv) * presupuesto_total
    return stake1, stake2

def calcular_ganancias_completas(a, b, x, y, win1, win2, place1, place2, commission=0.02):
    """Calcula ganancias para TODOS los escenarios incluyendo otros galgos"""
    com_factor = 1 - commission
    
    # Escenarios originales (G1 y G2 en 1ro y 2do)
    G1 = a*(win1-1) - b - x*(place1-1) + y*com_factor  # G1 gana, G2 no coloca
    G2 = -a + b*(win2-1) + x*com_factor - y*(place2-1)  # G2 gana, G1 no coloca
    G3 = -a + b*(win2-1) - x*(place1-1) - y*(place2-1)  # G1 2do, G2 gana
    G4 = a*(win1-1) - b - x*(place1-1) - y*(place2-1)   # G2 2do, G1 gana
    G5 = -a - b + x*com_factor + y*com_factor           # Ambos no colocan
    
    # NUEVOS ESCENARIOS - Otros galgos ganan
    G6 = -a - b + x*com_factor + y*com_factor           # Otro gana, ambos no colocan (igual a G5)
    G7 = -a - b - x*(place1-1) + y*com_factor           # Otro gana, G1 coloca (2do), G2 no coloca
    G8 = -a - b + x*com_factor - y*(place2-1)           # Otro gana, G2 coloca (2do), G1 no coloca
    G9 = -a - b - x*(place1-1) - y*(place2-1)           # Otro gana, ambos colocan (G1 y G2 2do y 3ro)
    
    return [G1, G2, G3, G4, G5, G6, G7, G8, G9]

def optimizacion_completa(win1, win2, place1, place2, commission=0.02):
    """Optimización considerando TODOS los escenarios"""
    a, b = calcular_stakes_ganador(win1, win2)
    com_factor = 1 - commission
    
    prob_place1 = 1 / place1
    prob_place2 = 1 / place2
    
    # Guess inicial más conservador
    base_lay1 = prob_place1 * 2.5
    base_lay2 = prob_place2 * 2.5
    
    best_stake1, best_stake2 = base_lay1, base_lay2
    best_score = -np.inf
    
    # Búsqueda más amplia y conservadora
    for x in np.arange(0.1, 3.0, 0.1):
        for y in np.arange(0.1, 3.0, 0.1):
            ganancias = calcular_ganancias_completas(a, b, x, y, win1, win2, place1, place2, commission)
            
            # Score: maximizar ganancia mínima, pero penalizar escenarios negativos
            ganancia_min = min(ganancias)
            escenarios_negativos = sum(1 for g in ganancias if g < 0)
            
            # Penalizar tener muchos escenarios negativos
            score = ganancia_min - (escenarios_negativos * 0.1)
            
            if score > best_score:
                best_score = score
                best_stake1, best_stake2 = x, y
    
    return a, b, best_stake1, best_stake2

# INTERFAZ STREAMLIT MEJORADA
st.set_page_config(page_title="Optimizador Completo", page_icon="🏁", layout="centered")

st.title("🏁 Optimizador COMPLETO - Todos los Escenarios")

st.info("🔍 **Ahora considera TODOS los escenarios posibles** - Incluyendo cuando otros galgos ganan")

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
if st.button("🎲 Calcular Estrategia Completa"):
    with st.spinner("Optimizando considerando todos los escenarios..."):
        stake_win1, stake_win2, stake_lay1, stake_lay2 = optimizacion_completa(
            win1, win2, place1, place2, commission
        )
        ganancias = calcular_ganancias_completas(
            stake_win1, stake_win2, stake_lay1, stake_lay2,
            win1, win2, place1, place2, commission
        )
    
    # MOSTRAR RESULTADOS
    st.header("💡 Estrategia Optimizada Completa")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Apuestas a Ganador")
        st.metric("Galgo 1", f"${stake_win1:.2f} @ {win1:.2f}")
        st.metric("Galgo 2", f"${stake_win2:.2f} @ {win2:.2f}")
    
    with col2:
        st.subheader("Lay a Colocado")
        st.metric("Contra Galgo 1", f"${stake_lay1:.2f}")
        st.metric("Contra Galgo 2", f"${stake_lay2:.2f}")
    
    # TABLA COMPLETA DE ESCENARIOS
    st.subheader("📈 TODOS los Escenarios Posibles")
    
    escenarios_completos = [
        "G1 gana, G2 no coloca",
        "G2 gana, G1 no coloca", 
        "G1 2do, G2 gana",
        "G2 2do, G1 gana",
        "Ambos no colocan",
        "🔥 OTRO gana, ambos NO colocan",
        "🔥 OTRO gana, G1 COLOCA (2do), G2 no coloca", 
        "🔥 OTRO gana, G2 COLOCA (2do), G1 no coloca",
        "🔥 OTRO gana, AMBOS COLOCAN (2do y 3ro)"
    ]
    
    resultados_completos = []
    for i, (esc, gan) in enumerate(zip(escenarios_completos, ganancias)):
        estilo = "🔥" if "OTRO" in esc else ""
        resultados_completos.append({
            'Escenario': f"{estilo} {esc}",
            'Ganancia/Neta': f"${gan:.3f}",
            'Resultado': "✅ Ganancia" if gan >= 0 else "⚠️ Pérdida"
        })
    
    df_completo = pd.DataFrame(resultados_completos)
    st.table(df_completo)
    
    # ESTADÍSTICAS COMPLETAS
    st.subheader("📊 Estadísticas Completas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_escenarios = len(ganancias)
        escenarios_ganadores = sum(1 for g in ganancias if g >= 0)
        st.metric("Escenarios Ganadores", f"{escenarios_ganadores}/{total_escenarios}")
    
    with col2:
        perdida_max = min(ganancias)
        st.metric("Pérdida Máxima", f"${perdida_max:.3f}")
    
    with col3:
        ganancia_promedio = np.mean(ganancias)
        st.metric("Ganancia Promedio", f"${ganancia_promedio:.3f}")
    
    # ANÁLISIS DE RIESGO
    with st.expander("🔍 Análisis Detallado de Riesgo"):
        st.write("**Nuevos escenarios considerados:**")
        st.write("1. **Otro galgo gana, ambos NO colocan** - Similar a 'Ambos no colocan'")
        st.write("2. **Otro gana, G1 coloca** - Perdemos Lay G1, ganamos Lay G2")
        st.write("3. **Otro gana, G2 coloca** - Ganamos Lay G1, perdemos Lay G2") 
        st.write("4. **Otro gana, ambos colocan** - Perdemos ambos Lay (peor escenario)")
        
        st.write(f"**Probabilidades estimadas (6 galgos):**")
        st.write(f"- G1 o G2 ganan: {((1/win1 + 1/win2)*100):.1f}%")
        st.write(f"- Otro galgo gana: {(1 - (1/win1 + 1/win2))*100:.1f}%")

st.markdown("---")
st.caption("⚠️ Herramienta educativa - Apueste responsablemente")
