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

def calcular_escenarios_con_g3(a, b, x, y, z, win1, win2, place1, place2, place3, commission=0.02):
    """Calcula escenarios con 3 galgos en Lay"""
    com_factor = 1 - commission
    
    escenarios = [
        # G1 gana, G2 no coloca, G3 no coloca
        a*(win1-1) - b - x*(place1-1) + y*com_factor + z*com_factor,
        
        # G2 gana, G1 no coloca, G3 no coloca  
        -a + b*(win2-1) + x*com_factor - y*(place2-1) + z*com_factor,
        
        # G1 2do, G2 gana, G3 no coloca
        -a + b*(win2-1) - x*(place1-1) - y*(place2-1) + z*com_factor,
        
        # G2 2do, G1 gana, G3 no coloca
        a*(win1-1) - b - x*(place1-1) - y*(place2-1) + z*com_factor,
        
        # G1 2do, G3 gana, G2 no coloca
        -a - b - x*(place1-1) + y*com_factor - z*(place3-1),
        
        # G2 2do, G3 gana, G1 no coloca
        -a - b + x*com_factor - y*(place2-1) - z*(place3-1),
        
        # G3 gana, G1 no coloca, G2 no coloca
        -a - b + x*com_factor + y*com_factor - z*(place3-1),
        
        # Todos no colocan
        -a - b + x*com_factor + y*com_factor + z*com_factor
    ]
    
    return escenarios

def optimizar_con_g3(win1, win2, place1, place2, place3, commission=0.02):
    """Optimización con 3 galgos en Lay"""
    a, b = calcular_stakes_ganador(win1, win2)
    
    best_x, best_y, best_z = 0.1, 0.1, 0.1
    best_score = -np.inf
    mejores_ganancias = []
    
    # Buscar combinación que minimice pérdidas
    for x in np.arange(0.1, 1.5, 0.1):
        for y in np.arange(0.1, 1.5, 0.1):
            for z in np.arange(0.1, 1.5, 0.1):
                ganancias = calcular_escenarios_con_g3(a, b, x, y, z, win1, win2, place1, place2, place3, commission)
                
                perdida_maxima = min(ganancias)
                ganancia_minima = min(ganancias)
                escenarios_negativos = sum(1 for g in ganancias if g < 0)
                
                # Score que premia menos pérdidas y menor pérdida máxima
                score = -perdida_maxima - (escenarios_negativos * 0.5) + ganancia_minima
                
                if score > best_score:
                    best_score = score
                    best_x, best_y, best_z = x, y, z
                    mejores_ganancias = ganancias
    
    return a, b, best_x, best_y, best_z, mejores_ganancias

# INTERFAZ STREAMLIT
st.set_page_config(page_title="Optimizador con G3", page_icon="🔧", layout="centered")

st.title("🔧 Optimizador con 3 Galgos en Lay")

st.info("**Estrategia: Agregar G3 en Lay para balancear pérdidas**")

# Entrada de datos
with st.sidebar:
    st.header("⚙️ Configuración")
    
    st.subheader("Galgos Principales (Back + Lay)")
    col1, col2 = st.columns(2)
    
    with col1:
        win1 = st.number_input("G1 - Ganar", value=5.8, min_value=1.0, key="win1")
        place1 = st.number_input("G1 - Colocado", value=2.62, min_value=1.0, key="place1")
    
    with col2:
        win2 = st.number_input("G2 - Ganar", value=7.0, min_value=1.0, key="win2")  
        place2 = st.number_input("G2 - Colocado", value=3.55, min_value=1.0, key="place2")
    
    st.subheader("Galgo 3 (Solo Lay)")
    place3 = st.number_input("G3 - Odd Colocado", value=1.67, min_value=1.0, key="place3")
    st.caption("G3 es solo para Lay, no para Back")
    
    presupuesto = st.number_input("💰 Presupuesto Back", value=2.0, min_value=1.0, step=0.5)
    commission = st.slider("🎯 Comisión Exchange (%)", 0.0, 10.0, 2.0) / 100

# Calcular estrategia
if st.button("🎲 Optimizar con G3", type="primary"):
    with st.spinner("Optimizando con 3 galgos en Lay..."):
        stake_win1, stake_win2, stake_lay1, stake_lay2, stake_lay3, ganancias = optimizar_con_g3(
            win1, win2, place1, place2, place3, commission
        )
    
    # MOSTRAR RESULTADOS
    st.header("💡 Estrategia con 3 Galgos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Back a Ganador")
        st.metric("Galgo 1", f"${stake_win1:.2f} @ {win1:.2f}")
        st.metric("Galgo 2", f"${stake_win2:.2f} @ {win2:.2f}")
    
    with col2:
        st.subheader("Lay Principales")
        st.metric("Contra G1", f"${stake_lay1:.2f}")
        st.metric("Contra G2", f"${stake_lay2:.2f}")
    
    with col3:
        st.subheader("Lay G3 (Balanceador)")
        st.metric("Contra G3", f"${stake_lay3:.2f}")
        st.caption(f"Odd: {place3:.2f}")

    # TABLA DE ESCENARIOS MEJORADA
    st.header("📈 Escenarios con G3")
    
    escenarios = [
        "G1 gana, G2/G3 no colocan",
        "G2 gana, G1/G3 no colocan", 
        "G1 2do, G2 gana, G3 no coloca",
        "G2 2do, G1 gana, G3 no coloca",
        "🔴 G1 2do, G3 gana, G2 no coloca",
        "🔴 G2 2do, G3 gana, G1 no coloca",
        "🔴 G3 gana, G1/G2 no colocan",
        "Todos no colocan"
    ]
    
    resultados = []
    for i, (esc, gan) in enumerate(zip(escenarios, ganancias)):
        if gan >= 0:
            estado = "✅ Ganancia"
        elif gan >= -1.0:
            estado = "⚠️ Pérdida Leve"
        else:
            estado = "🔴 Pérdida Grave"
            
        resultados.append({
            'Escenario': esc,
            'Ganancia/Neta': f"${gan:.3f}",
            'Resultado': estado
        })
    
    df_resultados = pd.DataFrame(resultados)
    st.table(df_resultados)
    
    # COMPARACIÓN CON/SIN G3
    st.header("📊 Comparación de Estrategias")
    
    # Calcular sin G3 para comparar
    def calcular_sin_g3(a, b, x, y, win1, win2, place1, place2, commission=0.02):
        com_factor = 1 - commission
        return [
            a*(win1-1) - b - x*(place1-1) + y*com_factor,
            -a + b*(win2-1) + x*com_factor - y*(place2-1),
            -a + b*(win2-1) - x*(place1-1) - y*(place2-1),
            a*(win1-1) - b - x*(place1-1) - y*(place2-1),
            -a - b - x*(place1-1) + y*com_factor,
            -a - b + x*com_factor - y*(place2-1),
            -a - b + x*com_factor + y*com_factor
        ]
    
    ganancias_sin_g3 = calcular_sin_g3(stake_win1, stake_win2, stake_lay1, stake_lay2, 
                                     win1, win2, place1, place2, commission)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔴 SIN G3")
        perdida_max_sin = min(ganancias_sin_g3)
        st.metric("Pérdida Máxima", f"${perdida_max_sin:.3f}")
        st.write(f"Escenarios graves: {sum(1 for g in ganancias_sin_g3 if g < -1.5)}/7")
    
    with col2:
        st.subheader("✅ CON G3")
        perdida_max_con = min(ganancias)
        st.metric("Pérdida Máxima", f"${perdida_max_con:.3f}")
        st.write(f"Escenarios graves: {sum(1 for g in ganancias if g < -1.5)}/8")
    
    # MEJORA PORCENTUAL
    mejora = ((perdida_max_con - perdida_max_sin) / abs(perdida_max_sin)) * 100
    st.metric("💪 Mejora en Pérdida Máxima", f"{mejora:+.1f}%")

st.markdown("---")
st.caption("⚠️ Herramienta educativa - Apueste responsablemente")
