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

def optimizacion_inteligente(win1, win2, place1, place2, commission=0.02):
    """Optimización con stakes prorrateados"""
    a, b = calcular_stakes_ganador(win1, win2)
    com_factor = 1 - commission
    
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
st.set_page_config(page_title="Optimizador con Ajuste", page_icon="🏁", layout="centered")

st.title("🏁 Optimizador con Ajuste de Stakes en Tiempo Real")

st.info("🎛️ **Ajusta las stakes y ve los resultados en tiempo real**")

# Entrada de datos en sidebar para más espacio
with st.sidebar:
    st.header("⚙️ Configuración")
    
    st.subheader("Odds de los Galgos")
    win1 = st.number_input("Galgo 1 - Odd a Ganar", value=3.10, min_value=1.0, key="win1")
    place1 = st.number_input("Galgo 1 - Odd a Colocado", value=1.80, min_value=1.0, key="place1")
    win2 = st.number_input("Galgo 2 - Odd a Ganar", value=10.00, min_value=1.0, key="win2")  
    place2 = st.number_input("Galgo 2 - Odd a Colocado", value=3.50, min_value=1.0, key="place2")
    
    presupuesto = st.number_input("💰 Presupuesto Total Back ($)", value=2.0, min_value=1.0, step=0.5)
    commission = st.slider("🎯 Comisión del Exchange (%)", 0.0, 10.0, 2.0) / 100

# Calcular stakes base una vez
if 'stakes_base' not in st.session_state:
    with st.spinner("Calculando estrategia base..."):
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
    "📈 Aumentar/Disminuir todas las stakes (%)",
    min_value=-50,
    max_value=200, 
    value=0,
    step=10,
    help="Ajusta todas las stakes por el mismo porcentaje"
)

# Aplicar ajuste a las stakes base
factor_ajuste = 1 + (ajuste_porcentaje / 100)

stake_win1_ajustado = st.session_state.stakes_base['win1'] * factor_ajuste
stake_win2_ajustado = st.session_state.stakes_base['win2'] * factor_ajuste  
stake_lay1_ajustado = st.session_state.stakes_base['lay1'] * factor_ajuste
stake_lay2_ajustado = st.session_state.stakes_base['lay2'] * factor_ajuste

# Calcular ganancias con stakes ajustadas
ganancias_ajustadas = calcular_ganancias(
    stake_win1_ajustado, stake_win2_ajustado,
    stake_lay1_ajustado, stake_lay2_ajustado,
    win1, win2, place1, place2, commission
)

# MOSTRAR RESULTADOS ACTUALIZADOS
st.header("💡 Estrategia con Stakes Ajustadas")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Apuestas a Ganador")
    st.metric("Galgo 1", f"${stake_win1_ajustado:.2f}", 
              f"{ajuste_porcentaje:+.0f}%" if ajuste_porcentaje != 0 else "")
    st.metric("Galgo 2", f"${stake_win2_ajustado:.2f}",
              f"{ajuste_porcentaje:+.0f}%" if ajuste_porcentaje != 0 else "")

with col2:
    st.subheader("Lay a Colocado")
    st.metric("Contra Galgo 1", f"${stake_lay1_ajustado:.2f}",
              f"{ajuste_porcentaje:+.0f}%" if ajuste_porcentaje != 0 else "")
    st.metric("Contra Galgo 2", f"${stake_lay2_ajustado:.2f}", 
              f"{ajuste_porcentaje:+.0f}%" if ajuste_porcentaje != 0 else "")

with col3:
    st.subheader("📊 Resumen Financiero")
    inversion_total = (stake_win1_ajustado + stake_win2_ajustado + 
                      stake_lay1_ajustado + stake_lay2_ajustado)
    st.metric("Inversión Total", f"${inversion_total:.2f}",
              f"{((inversion_total / (stake_win1_ajustado/factor_ajuste + stake_win2_ajustado/factor_ajuste + stake_lay1_ajustado/factor_ajuste + stake_lay2_ajustado/factor_ajuste)) - 1) * 100:+.0f}%")
    
    perdida_max = min(ganancias_ajustadas)
    st.metric("Pérdida Máxima", f"${perdida_max:.3f}")

# TABLA DE ESCENARIOS ACTUALIZADA
st.subheader("📈 Resultados por Escenario (Actualizado)")

escenarios = [
    "G1 gana, G2 no coloca",
    "G2 gana, G1 no coloca", 
    "G1 2do, G2 gana",
    "G2 2do, G1 gana",
    "Ambos no colocan"
]

resultados_ajustados = []
for i, (esc, gan) in enumerate(zip(escenarios, ganancias_ajustadas)):
    # Calcular cambio porcentual vs base
    gan_base = calcular_ganancias(
        st.session_state.stakes_base['win1'], st.session_state.stakes_base['win2'],
        st.session_state.stakes_base['lay1'], st.session_state.stakes_base['lay2'],
        win1, win2, place1, place2, commission
    )[i]
    
    cambio = ((gan - gan_base) / abs(gan_base)) * 100 if gan_base != 0 else 0
    
    resultados_ajustados.append({
        'Escenario': esc,
        'Ganancia/Neta': f"${gan:.3f}",
        'Cambio vs Base': f"{cambio:+.1f}%" if ajuste_porcentaje != 0 else "0%",
        'Resultado': "✅ Ganancia" if gan >= 0 else "⚠️ Pérdida"
    })

df_resultados_ajustados = pd.DataFrame(resultados_ajustados)
st.table(df_resultados_ajustados)

# GRÁFICO DE COMPARACIÓN
st.subheader("📊 Comparación vs Stakes Base")

col1, col2 = st.columns(2)

with col1:
    st.write("**Stakes Base (100%)**")
    st.write(f"- Back G1: ${st.session_state.stakes_base['win1']:.2f}")
    st.write(f"- Back G2: ${st.session_state.stakes_base['win2']:.2f}")
    st.write(f"- Lay G1: ${st.session_state.stakes_base['lay1']:.2f}")
    st.write(f"- Lay G2: ${st.session_state.stakes_base['lay2']:.2f}")

with col2:
    st.write(f"**Stakes Ajustadas ({100+ajuste_porcentaje}%)**")
    st.write(f"- Back G1: ${stake_win1_ajustado:.2f}")
    st.write(f"- Back G2: ${stake_win2_ajustado:.2f}") 
    st.write(f"- Lay G1: ${stake_lay1_ajustado:.2f}")
    st.write(f"- Lay G2: ${stake_lay2_ajustado:.2f}")

# BOTÓN PARA RECALCULAR BASE
if st.button("🔄 Recalcular Estrategia Base"):
    with st.spinner("Recalculando..."):
        stake_win1_base, stake_win2_base, stake_lay1_base, stake_lay2_base = optimizacion_inteligente(
            win1, win2, place1, place2, commission
        )
    st.session_state.stakes_base = {
        'win1': stake_win1_base,
        'win2': stake_win2_base,
        'lay1': stake_lay1_base, 
        'lay2': stake_lay2_base
    }
    st.rerun()

st.markdown("---")
st.caption("⚠️ Herramienta educativa - Apueste responsablemente")
