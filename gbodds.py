import streamlit as st
import pandas as pd
import numpy as np

def calcular_stakes_ganador(win1, win2, presupuesto_total=2.0):
    """Prorratea los stakes a ganador según las odds"""
    inv1 = 1 / win1
    inv2 = 1 / win2
    total_inv = inv1 + inv2
    stake1 = (inv1 / total_inv) * presupuesto_total
    stake2 = (inv2 / total_inv) * presupuesto_total
    return stake1, stake2

def calcular_todos_escenarios(a, b, x, y, win1, win2, place1, place2, commission=0.02):
    """Calcula TODOS los 7 escenarios posibles"""
    com_factor = 1 - commission
    
    # ESCENARIO 1: G1 gana, G2 no coloca
    G1 = a*(win1-1) - b - x*(place1-1) + y*com_factor
    
    # ESCENARIO 2: G2 gana, G1 no coloca
    G2 = -a + b*(win2-1) + x*com_factor - y*(place2-1)
    
    # ESCENARIO 3: G1 2do, G2 gana (ambos se colocan)
    G3 = -a + b*(win2-1) - x*(place1-1) - y*(place2-1)
    
    # ESCENARIO 4: G2 2do, G1 gana (ambos se colocan)
    G4 = a*(win1-1) - b - x*(place1-1) - y*(place2-1)
    
    # ESCENARIO 5: G1 2do, OTRO galgo gana
    G5 = -a - b - x*(place1-1) + y*com_factor
    
    # ESCENARIO 6: G2 2do, OTRO galgo gana
    G6 = -a - b + x*com_factor - y*(place2-1)
    
    # ESCENARIO 7: Ambos no colocan
    G7 = -a - b + x*com_factor + y*com_factor
    
    return [G1, G2, G3, G4, G5, G6, G7]

def optimizar_stakes_completo(win1, win2, place1, place2, commission=0.02):
    """Optimización considerando TODOS los escenarios"""
    a, b = calcular_stakes_ganador(win1, win2)
    
    # Búsqueda grid exhaustiva
    best_x, best_y = 0, 0
    best_score = -np.inf
    
    for x in np.arange(0.1, 3.0, 0.05):
        for y in np.arange(0.1, 3.0, 0.05):
            ganancias = calcular_todos_escenarios(a, b, x, y, win1, win2, place1, place2, commission)
            
            # Score: maximizar la ganancia mínima y minimizar pérdidas grandes
            ganancia_min = min(ganancias)
            perdida_max = abs(min([0] + [g for g in ganancias if g < 0]))
            
            # Penalizar pérdidas grandes, premiar ganancias consistentes
            score = ganancia_min - (perdida_max * 0.1)
            
            if score > best_score:
                best_score = score
                best_x, best_y = x, y
    
    return a, b, best_x, best_y

# INTERFAZ STREAMLIT
st.set_page_config(page_title="Optimizador Completo", page_icon="🏁", layout="centered")

st.title("🏁 Optimizador COMPLETO - 7 Escenarios")

st.info("🔍 **Ahora considera TODOS los escenarios posibles**")

# Entrada de datos
with st.sidebar:
    st.header("⚙️ Configuración")
    
    st.subheader("Odds de los Galgos")
    col1, col2 = st.columns(2)
    
    with col1:
        win1 = st.number_input("G1 - Ganar", value=5.8, min_value=1.0, key="win1")
        place1 = st.number_input("G1 - Colocado", value=2.62, min_value=1.0, key="place1")
    
    with col2:
        win2 = st.number_input("G2 - Ganar", value=7.0, min_value=1.0, key="win2")  
        place2 = st.number_input("G2 - Colocado", value=3.55, min_value=1.0, key="place2")
    
    presupuesto = st.number_input("💰 Presupuesto Back", value=2.0, min_value=1.0, step=0.5)
    commission = st.slider("🎯 Comisión Exchange (%)", 0.0, 10.0, 2.0) / 100

# Calcular estrategia
if st.button("🎲 Calcular Estrategia Completa", type="primary"):
    with st.spinner("Optimizando considerando todos los escenarios..."):
        stake_win1, stake_win2, stake_lay1, stake_lay2 = optimizar_stakes_completo(
            win1, win2, place1, place2, commission
        )
        ganancias = calcular_todos_escenarios(
            stake_win1, stake_win2, stake_lay1, stake_lay2,
            win1, win2, place1, place2, commission
        )
    
    # MOSTRAR RESULTADOS
    st.header("💡 Estrategia Optimizada")
    
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
    st.header("📈 TODOS los Escenarios Posibles")
    
    escenarios = [
        "G1 gana, G2 no coloca",
        "G2 gana, G1 no coloca", 
        "G1 2do, G2 gana (ambos colocados)",
        "G2 2do, G1 gana (ambos colocados)",
        "🔴 G1 2do, OTRO galgo gana",
        "🔴 G2 2do, OTRO galgo gana",
        "Ambos no colocan"
    ]
    
    resultados = []
    for i, (esc, gan) in enumerate(zip(escenarios, ganancias)):
        resultado = {
            'Escenario': esc,
            'Ganancia/Neta': f"${gan:.3f}",
            'Resultado': "✅ Ganancia" if gan >= 0 else "⚠️ Pérdida Leve" if gan >= -1 else "🔴 Pérdida Grave"
        }
        resultados.append(resultado)
    
    df_resultados = pd.DataFrame(resultados)
    st.table(df_resultados)
    
    # ANÁLISIS ESTADÍSTICO
    st.header("📊 Análisis Estadístico Completo")
    
    escenarios_ganadores = sum(1 for g in ganancias if g >= 0)
    escenarios_perdedores = len(ganancias) - escenarios_ganadores
    perdida_maxima = min(ganancias)
    ganancia_maxima = max(ganancias)
    ganancia_promedio = np.mean(ganancias)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Escenarios Ganadores", f"{escenarios_ganadores}/7")
    
    with col2:
        st.metric("Pérdida Máxima", f"${perdida_maxima:.3f}")
    
    with col3:
        st.metric("Ganancia Máxima", f"${ganancia_maxima:.3f}")
    
    with col4:
        st.metric("Ganancia Promedio", f"${ganancia_promedio:.3f}")
    
    # RECOMENDACIÓN FINAL
    st.header("🎯 Recomendación Final")
    
    if ganancia_promedio > 0 and perdida_maxima > -2:
        st.success("✅ **STRATEGIA VIABLE** - Valor esperado positivo y riesgo controlado")
    elif ganancia_promedio > 0:
        st.warning("⚠️ **STRATEGIA RIESGOSA** - Valor positivo pero pérdidas potenciales altas")
    else:
        st.error("🔴 **NO RECOMENDADO** - Valor esperado negativo")

# EXPLICACIÓN DE ESCENARIOS
with st.expander("📖 Explicación de los 7 Escenarios"):
    st.write("""
    **1. G1 gana, G2 no coloca** - Solo G1 se coloca (1ro)
    **2. G2 gana, G1 no coloca** - Solo G2 se coloca (1ro)  
    **3. G1 2do, G2 gana** - Ambos se colocan (G2 1ro, G1 2do)
    **4. G2 2do, G1 gana** - Ambos se colocan (G1 1ro, G2 2do)
    **5. G1 2do, OTRO gana** - G1 se coloca pero otro galgo gana
    **6. G2 2do, OTRO gana** - G2 se coloca pero otro galgo gana
    **7. Ambos no colocan** - Ninguno termina 1ro o 2do
    """)

st.markdown("---")
st.caption("⚠️ Herramienta educativa - Apueste responsablemente")
