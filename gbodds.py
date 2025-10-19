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
st.set_page_config(page_title="Optimizador con Ajuste", page_icon="🎚️", layout="centered")

st.title("🎚️ Optimizador con Ajuste de Stakes en Tiempo Real")

st.info("💰 **Ajusta todas las stakes con un solo control** - Ve el impacto inmediato")

with st.sidebar:
    st.header("⚙️ Configuración Base")
    
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

# Calcular estrategia base
if 'stakes_base' not in st.session_state or st.button("🔄 Calcular Estrategia Base"):
    with st.spinner("Calculando estrategia óptima base..."):
        stake_win1_base, stake_win2_base, stake_lay1_base, stake_lay2_base = optimizacion_minimizar_perdidas(
            win1, win2, place1, place2, commission
        )
    st.session_state.stakes_base = {
        'win1': stake_win1_base,
        'win2': stake_win2_base, 
        'lay1': stake_lay1_base,
        'lay2': stake_lay2_base
    }
    st.session_state.ganancias_base = calcular_ganancias_reales(
        stake_win1_base, stake_win2_base, stake_lay1_base, stake_lay2_base,
        win1, win2, place1, place2, commission
    )

# CONTROL DE AJUSTE PORCENTUAL
st.header("🎚️ Ajuste de Stakes en Tiempo Real")

ajuste_porcentaje = st.slider(
    "📈 Ajustar TODAS las stakes (%)",
    min_value=-50,
    max_value=200, 
    value=0,
    step=10,
    help="Aumenta o disminuye todas las stakes por el mismo porcentaje"
)

# Aplicar ajuste a las stakes base
if 'stakes_base' in st.session_state:
    factor_ajuste = 1 + (ajuste_porcentaje / 100)
    
    stake_win1_ajustado = st.session_state.stakes_base['win1'] * factor_ajuste
    stake_win2_ajustado = st.session_state.stakes_base['win2'] * factor_ajuste  
    stake_lay1_ajustado = st.session_state.stakes_base['lay1'] * factor_ajuste
    stake_lay2_ajustado = st.session_state.stakes_base['lay2'] * factor_ajuste
    
    # Calcular ganancias con stakes ajustadas
    ganancias_ajustadas = calcular_ganancias_reales(
        stake_win1_ajustado, stake_win2_ajustado,
        stake_lay1_ajustado, stake_lay2_ajustado,
        win1, win2, place1, place2, commission
    )

    # MOSTRAR RESULTADOS ACTUALIZADOS
    st.header("💡 Estrategia con Stakes Ajustadas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Back a Ganador")
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
        st.subheader("📊 Impacto Financiero")
        inversion_base = (st.session_state.stakes_base['win1'] + st.session_state.stakes_base['win2'] + 
                         st.session_state.stakes_base['lay1'] + st.session_state.stakes_base['lay2'])
        inversion_ajustada = (stake_win1_ajustado + stake_win2_ajustado + 
                             stake_lay1_ajustado + stake_lay2_ajustado)
        st.metric("Inversión Total", f"${inversion_ajustada:.2f}",
                 f"{((inversion_ajustada/inversion_base)-1)*100:+.0f}%")
        
        perdida_max = min(ganancias_ajustadas)
        st.metric("Pérdida Máxima", f"${perdida_max:.3f}")

    # TABLA DE ESCENARIOS ACTUALIZADA
    st.subheader("📈 Escenarios Reales - Con Stakes Ajustadas")
    
    escenarios_reales = [
        "G1 gana, G2 no coloca",
        "G2 gana, G1 no coloca", 
        "G1 2do, G2 gana",
        "G2 2do, G1 gana",
        "Ambos no colocan",
        "OTRO gana, G1 2do, G2 no coloca",
        "OTRO gana, G2 2do, G1 no coloca"
    ]
    
    resultados_ajustados = []
    for i, (esc, gan) in enumerate(zip(escenarios_reales, ganancias_ajustadas)):
        # Calcular cambio vs base
        gan_base = st.session_state.ganancias_base[i]
        cambio_porcentual = ((gan - gan_base) / abs(gan_base)) * 100 if gan_base != 0 else 0
        
        resultados_ajustados.append({
            'Escenario': esc,
            'Ganancia/Neta': f"${gan:.3f}",
            'Cambio vs Base': f"{cambio_porcentual:+.1f}%" if ajuste_porcentaje != 0 else "0%",
            'Resultado': "✅ Ganancia" if gan >= 0 else "⚠️ Pérdida"
        })
    
    st.table(pd.DataFrame(resultados_ajustados))

    # COMPARACIÓN LADO A LADO
    st.subheader("🔄 Comparación: Base vs Ajustada")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🏠 Stakes Base (100%)**")
        st.write(f"- Back G1: ${st.session_state.stakes_base['win1']:.2f}")
        st.write(f"- Back G2: ${st.session_state.stakes_base['win2']:.2f}")
        st.write(f"- Lay G1: ${st.session_state.stakes_base['lay1']:.2f}")
        st.write(f"- Lay G2: ${st.session_state.stakes_base['lay2']:.2f}")
        st.write(f"**Pérdida máxima:** ${min(st.session_state.ganancias_base):.3f}")
    
    with col2:
        st.write(f"**🎯 Stakes Ajustadas ({100+ajuste_porcentaje}%)**")
        st.write(f"- Back G1: ${stake_win1_ajustado:.2f}")
        st.write(f"- Back G2: ${stake_win2_ajustado:.2f}") 
        st.write(f"- Lay G1: ${stake_lay1_ajustado:.2f}")
        st.write(f"- Lay G2: ${stake_lay2_ajustado:.2f}")
        st.write(f"**Pérdida máxima:** ${min(ganancias_ajustadas):.3f}")

    # GUÍA DE AJUSTE
    with st.expander("💡 Guía de Ajuste de Stakes"):
        st.write("""
        **🔽 Disminuir stakes (-50% a 0%):**
        - ✅ Menor inversión total
        - ✅ Menor riesgo absoluto  
        - ❌ Menores ganancias potenciales
        - ❌ Pérdidas más frecuentes en escenarios marginales
        
        **🔼 Aumentar stakes (0% a +200%):**
        - ✅ Mayores ganancias en escenarios favorables
        - ✅ Mejor protección en escenarios desfavorables
        - ❌ Mayor inversión requerida
        - ❌ Pérdidas más grandes si ocurren escenarios negativos
        
        **Recomendación:** Empieza con la estrategia base (0%) y ajusta según tu tolerancia al riesgo.
        """)

else:
    st.warning("⚠️ Primero calcula la estrategia base haciendo click en 'Calcular Estrategia Base'")

st.markdown("---")
st.caption("⚠️ Herramienta educativa - Apueste responsablemente")
