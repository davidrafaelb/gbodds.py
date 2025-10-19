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
    
    escenarios = [
        a*(win1-1) - b - x*(place1-1) + y*com_factor,  # 1: G1 gana, G2 no
        -a + b*(win2-1) + x*com_factor - y*(place2-1), # 2: G2 gana, G1 no
        -a + b*(win2-1) - x*(place1-1) - y*(place2-1), # 3: G1 2do, G2 gana
        a*(win1-1) - b - x*(place1-1) - y*(place2-1),  # 4: G2 2do, G1 gana
        -a - b - x*(place1-1) + y*com_factor,          # 5: G1 2do, OTRO gana
        -a - b + x*com_factor - y*(place2-1),          # 6: G2 2do, OTRO gana
        -a - b + x*com_factor + y*com_factor           # 7: Ambos no
    ]
    
    return escenarios

def optimizar_sin_perdidas_grandes(win1, win2, place1, place2, commission=0.02):
    """Optimización AGRESIVA contra pérdidas grandes"""
    a, b = calcular_stakes_ganador(win1, win2)
    
    best_x, best_y = 0.1, 0.1
    best_score = -np.inf
    mejores_ganancias = []
    
    # Rangos más conservadores para evitar pérdidas
    for x in np.arange(0.1, 2.0, 0.05):  # Reducido máximo a 2.0
        for y in np.arange(0.1, 2.0, 0.05):
            ganancias = calcular_todos_escenarios(a, b, x, y, win1, win2, place1, place2, commission)
            
            # Penalización MUY FUERTE para pérdidas grandes
            perdida_maxima = min(ganancias)
            ganancia_minima = min(ganancias)
            ganancia_promedio = np.mean(ganancias)
            
            # Score que CASTIGA fuertemente cualquier pérdida > -1
            if perdida_maxima < -1.5:
                score = perdida_maxima * 10  # Castigo enorme
            elif perdida_maxima < -1.0:
                score = perdida_maxima * 5   # Castigo grande
            elif perdida_maxima < -0.5:
                score = perdida_maxima * 2   # Castigo moderado
            else:
                # Premiar ganancia mínima y promedio
                score = ganancia_minima + (ganancia_promedio * 0.5)
            
            if score > best_score:
                best_score = score
                best_x, best_y = x, y
                mejores_ganancias = ganancias
    
    return a, b, best_x, best_y, mejores_ganancias

def encontrar_stakes_conservadoras(win1, win2, place1, place2, commission=0.02):
    """Encuentra stakes que EVITEN pérdidas grandes"""
    a, b = calcular_stakes_ganador(win1, win2)
    
    # Probar combinaciones MUY conservadoras
    mejores_stakes = []
    
    for max_stake in [0.5, 0.8, 1.0, 1.2, 1.5]:
        for x in np.arange(0.1, max_stake, 0.1):
            for y in np.arange(0.1, max_stake, 0.1):
                ganancias = calcular_todos_escenarios(a, b, x, y, win1, win2, place1, place2, commission)
                perdida_maxima = min(ganancias)
                
                # Solo considerar combinaciones con pérdida máxima > -1
                if perdida_maxima > -1.0:
                    ganancia_promedio = np.mean(ganancias)
                    mejores_stakes.append((x, y, ganancia_promedio, perdida_maxima, ganancias))
    
    if mejores_stakes:
        # Ordenar por mejor ganancia promedio
        mejores_stakes.sort(key=lambda x: x[2], reverse=True)
        x, y, _, _, ganancias = mejores_stakes[0]
        return a, b, x, y, ganancias
    else:
        # Si no hay sin pérdidas, usar la menos mala
        return optimizar_sin_perdidas_grandes(win1, win2, place1, place2, commission)

# INTERFAZ STREAMLIT
st.set_page_config(page_title="Optimizador Sin Pérdidas", page_icon="🛡️", layout="centered")

st.title("🛡️ Optimizador SIN Pérdidas Graves")

st.warning("**OBJETIVO: Eliminar pérdidas > $1.00**")

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
    
    estrategia = st.radio("🎯 Estrategia:", 
                         ["Sin Pérdidas Graves (> -$1.00)", "Optimización Balanceada"])

# Calcular estrategia
if st.button("🎲 Encontrar Stakes Seguras", type="primary"):
    
    if estrategia == "Sin Pérdidas Graves (> -$1.00)":
        with st.spinner("Buscando stakes SIN pérdidas grandes..."):
            stake_win1, stake_win2, stake_lay1, stake_lay2, ganancias = encontrar_stakes_conservadoras(
                win1, win2, place1, place2, commission
            )
    else:
        with st.spinner("Optimizando balanceadamente..."):
            stake_win1, stake_win2, stake_lay1, stake_lay2, ganancias = optimizar_sin_perdidas_grandes(
                win1, win2, place1, place2, commission
            )
    
    # MOSTRAR RESULTADOS
    st.header("💡 Estrategia con Riesgo Controlado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Apuestas a Ganador")
        st.metric("Galgo 1", f"${stake_win1:.2f} @ {win1:.2f}")
        st.metric("Galgo 2", f"${stake_win2:.2f} @ {win2:.2f}")
    
    with col2:
        st.subheader("Lay a Colocado")
        st.metric("Contra Galgo 1", f"${stake_lay1:.2f}")
        st.metric("Contra Galgo 2", f"${stake_lay2:.2f}")
        st.caption(f"Stakes reducidas para controlar riesgo")

    # TABLA DE ESCENARIOS
    st.header("📈 Resultados - Riesgo Controlado")
    
    escenarios = [
        "G1 gana, G2 no coloca",
        "G2 gana, G1 no coloca", 
        "G1 2do, G2 gana",
        "G2 2do, G1 gana",
        "G1 2do, OTRO galgo gana",
        "G2 2do, OTRO galgo gana",
        "Ambos no colocan"
    ]
    
    resultados = []
    for i, (esc, gan) in enumerate(zip(escenarios, ganancias)):
        if gan >= 0:
            estado = "✅ Ganancia"
        elif gan >= -0.5:
            estado = "⚠️ Pérdida Leve" 
        elif gan >= -1.0:
            estado = "🔴 Pérdida Moderada"
        else:
            estado = "💀 Pérdida Grave"
            
        resultados.append({
            'Escenario': esc,
            'Ganancia/Neta': f"${gan:.3f}",
            'Resultado': estado
        })
    
    df_resultados = pd.DataFrame(resultados)
    st.table(df_resultados)
    
    # ANÁLISIS DE RIESGO
    st.header("🛡️ Análisis de Riesgo")
    
    perdida_maxima = min(ganancias)
    escenarios_graves = sum(1 for g in ganancias if g < -1.0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Pérdida Máxima", f"${perdida_maxima:.3f}")
        if perdida_maxima > -1.0:
            st.success("✅ Riesgo controlado")
        elif perdida_maxima > -2.0:
            st.warning("⚠️ Riesgo moderado")
        else:
            st.error("🔴 Riesgo alto")
    
    with col2:
        st.metric("Escenarios Graves", f"{escenarios_graves}/7")
        if escenarios_graves == 0:
            st.success("✅ Sin pérdidas graves")
        else:
            st.error(f"🔴 {escenarios_graves} escenario(s) con pérdida > $1.00")

    # RECOMENDACIÓN
    st.header("🎯 Recomendación Final")
    
    if perdida_maxima > -0.5:
        st.success("""
        **✅ ESTRATEGIA SEGURA**
        - Pérdidas máximas muy controladas
        - Riesgo aceptable
        - Puedes ejecutar con confianza
        """)
    elif perdida_maxima > -1.0:
        st.warning("""
        **⚠️ ESTRATEGIA MODERADA** 
        - Pérdidas controladas bajo $1.00
        - Riesgo manejable
        - Considerar ejecutar
        """)
    else:
        st.error("""
        **🔴 ESTRATEGIA RIESGOSA**
        - Pérdidas potenciales altas
        - No recomendada
        - Considerar otras odds
        """)

st.markdown("---")
st.caption("⚠️ Herramienta educativa - Apueste responsablemente")
