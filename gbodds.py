import streamlit as st
import pandas as pd
import numpy as np

def calcular_stakes_ganador(win1, win2, presupuesto_total=2.0):
    """Prorratea los stakes a ganador según las odds - CORREGIDO"""
    # Para odds iguales, stakes iguales
    if abs(win1 - win2) < 0.01:  # Si las odds son iguales
        stake1 = presupuesto_total / 2
        stake2 = presupuesto_total / 2
    else:
        # Usar el método de valor esperado para prorrateo más inteligente
        # Dar más stake a la odd con mejor valor (mayor odd)
        valor1 = win1 * (1/win1)  # = 1, pero ajustamos por probabilidad
        valor2 = win2 * (1/win2)  # = 1
        
        # En realidad, para back bets, queremos más stake en la odd con mayor valor esperado
        # Pero como ambas tienen valor esperado similar, usamos un enfoque diferente
        # Vamos a dar más stake a la odd más baja (más probable)
        inv1 = 1 / win1
        inv2 = 1 / win2
        total_inv = inv1 + inv2
        stake1 = (inv1 / total_inv) * presupuesto_total
        stake2 = (inv2 / total_inv) * presupuesto_total
    
    return stake1, stake2

def optimizacion_inteligente(win1, win2, place1, place2, commission=0.02):
    """Optimización con stakes prorrateados - CORREGIDO"""
    a, b = calcular_stakes_ganador(win1, win2)
    com_factor = 1 - commission
    
    # DEBUG: Mostrar cómo se calculan las stakes
    print(f"DEBUG: win1={win1}, win2={win2}, stake1={a:.2f}, stake2={b:.2f}")
    
    prob_place1 = 1 / place1
    prob_place2 = 1 / place2
    
    base_lay1 = prob_place1 * 3.0
    base_lay2 = prob_place2 * 3.0
    
    if prob_place1 > prob_place2:
        stake_lay1 = min(base_lay1, 2.5)
        stake_lay2 = max(base_lay2 * 0.3, 0.2)
    else:
        stake_lay1 = max(base_lay1 * 0.3, 0.2)
        stake_lay2 = min(base_lay2, 2.5)
    
    best_stake1, best_stake2 = stake_lay1, stake_lay2
    best_perdida_max = float('inf')
    
    for ajuste1 in np.arange(-0.5, 0.5, 0.1):
        for ajuste2 in np.arange(-0.3, 0.3, 0.1):
            test_stake1 = max(0.1, stake_lay1 + ajuste1)
            test_stake2 = max(0.1, stake_lay2 + ajuste2)
            
            G1 = a*(win1-1) - b - test_stake1*(place1-1) + test_stake2*com_factor
            G2 = -a + b*(win2-1) + test_stake1*com_factor - test_stake2*(place2-1)
            G3 = -a + b*(win2-1) - test_stake1*(place1-1) - test_stake2*(place2-1)
            G4 = a*(win1-1) - b - test_stake1*(place1-1) - test_stake2*(place2-1)
            G5 = -a - b + test_stake1*com_factor + test_stake2*com_factor
            
            perdida_max = min([G1, G2, G3, G4, G5])
            
            if perdida_max > best_perdida_max:
                best_perdida_max = perdida_max
                best_stake1, best_stake2 = test_stake1, test_stake2
    
    return a, b, best_stake1, best_stake2

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
st.set_page_config(page_title="Optimizador Corregido", page_icon="🏁", layout="centered")

st.title("🏁 Optimizador con Stakes Corregidas")

st.info("🔧 **Cálculo de stakes corregido** - Odds iguales = Stakes iguales")

# Entrada de datos en sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    
    st.subheader("Odds de los Galgos")
    col1, col2 = st.columns(2)
    
    with col1:
        win1 = st.number_input("G1 - Ganar", value=4.0, min_value=1.0, key="win1")
        place1 = st.number_input("G1 - Colocado", value=2.0, min_value=1.0, key="place1")
    
    with col2:
        win2 = st.number_input("G2 - Ganar", value=4.0, min_value=1.0, key="win2")  
        place2 = st.number_input("G2 - Colocado", value=2.0, min_value=1.0, key="place2")
    
    presupuesto = st.number_input("💰 Presupuesto Total Back ($)", value=2.0, min_value=1.0, step=0.5)
    commission = st.slider("🎯 Comisión del Exchange (%)", 0.0, 10.0, 2.0) / 100

# Calcular stakes base
if 'stakes_base' not in st.session_state or st.button("🔄 Calcular Nueva Estrategia"):
    with st.spinner("Calculando estrategia óptima..."):
        stake_win1_base, stake_win2_base, stake_lay1_base, stake_lay2_base = optimizacion_inteligente(
            win1, win2, place1, place2, commission
        )
    st.session_state.stakes_base = {
        'win1': stake_win1_base,
        'win2': stake_win2_base, 
        'lay1': stake_lay1_base,
        'lay2': stake_lay2_base
    }

# Control de ajuste de stakes
st.header("🎛️ Ajuste de Stakes")

ajuste_porcentaje = st.slider(
    "📈 Ajustar todas las stakes (%)",
    min_value=-50,
    max_value=200, 
    value=0,
    step=10
)

# Aplicar ajuste
factor_ajuste = 1 + (ajuste_porcentaje / 100)

stake_win1_ajustado = st.session_state.stakes_base['win1'] * factor_ajuste
stake_win2_ajustado = st.session_state.stakes_base['win2'] * factor_ajuste  
stake_lay1_ajustado = st.session_state.stakes_base['lay1'] * factor_ajuste
stake_lay2_ajustado = st.session_state.stakes_base['lay2'] * factor_ajuste

# Calcular ganancias
ganancias_ajustadas = calcular_ganancias(
    stake_win1_ajustado, stake_win2_ajustado,
    stake_lay1_ajustado, stake_lay2_ajustado,
    win1, win2, place1, place2, commission
)

# MOSTRAR RESULTADOS
st.header("💡 Estrategia con Stakes Ajustadas")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Apuestas a Ganador")
    
    # Verificar si las stakes son iguales para odds iguales
    if abs(win1 - win2) < 0.01:
        st.success("✅ Odds iguales - Stakes iguales")
    else:
        st.info("ℹ️ Odds diferentes - Stakes prorrateadas")
    
    st.metric("Galgo 1", f"${stake_win1_ajustado:.2f} @ {win1:.2f}",
              f"{ajuste_porcentaje:+.0f}%" if ajuste_porcentaje != 0 else "")
    st.metric("Galgo 2", f"${stake_win2_ajustado:.2f} @ {win2:.2f}",
              f"{ajuste_porcentaje:+.0f}%" if ajuste_porcentaje != 0 else "")
    
    # Mostrar cálculo de prorrateo
    with st.expander("📐 Ver cálculo de prorrateo"):
        stake1_base, stake2_base = calcular_stakes_ganador(win1, win2, presupuesto)
        st.write(f"**Método de prorrateo:**")
        st.write(f"- Probabilidad implícita G1: {1/win1:.3f} ({1/win1*100:.1f}%)")
        st.write(f"- Probabilidad implícita G2: {1/win2:.3f} ({1/win2*100:.1f}%)")
        st.write(f"- Stake G1: ({1/win1:.3f} / {1/win1 + 1/win2:.3f}) × ${presupuesto} = ${stake1_base:.2f}")
        st.write(f"- Stake G2: ({1/win2:.3f} / {1/win1 + 1/win2:.3f}) × ${presupuesto} = ${stake2_base:.2f}")

with col2:
    st.subheader("Lay a Colocado")
    st.metric("Contra Galgo 1", f"${stake_lay1_ajustado:.2f}",
              f"{ajuste_porcentaje:+.0f}%" if ajuste_porcentaje != 0 else "")
    st.metric("Contra Galgo 2", f"${stake_lay2_ajustado:.2f}", 
              f"{ajuste_porcentaje:+.0f}%" if ajuste_porcentaje != 0 else "")

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
for i, (esc, gan) in enumerate(zip(escenarios, ganancias_ajustadas)):
    resultados.append({
        'Escenario': esc,
        'Ganancia/Neta': f"${gan:.3f}",
        'Resultado': "✅ Ganancia" if gan >= 0 else "⚠️ Pérdida"
    })

df_resultados = pd.DataFrame(resultados)
st.table(df_resultados)

# VERIFICACIÓN DE CONSISTENCIA
if abs(win1 - win2) < 0.01 and abs(stake_win1_ajustado - stake_win2_ajustado) > 0.01:
    st.error("🚨 **INCONSISTENCIA DETECTADA:** Odds iguales pero stakes diferentes!")
    st.write(f"G1 Stake: ${stake_win1_ajustado:.2f}, G2 Stake: ${stake_win2_ajustado:.2f}")
    st.write("Esto indica un error en el cálculo de prorrateo.")

st.markdown("---")
st.caption("⚠️ Herramienta educativa - Apueste responsablemente")
