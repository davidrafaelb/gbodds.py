import streamlit as st
import pandas as pd
import numpy as np
from itertools import combinations

def calcular_probabilidades(odds, total_colocados):
    """Convertir odds a probabilidades implícitas y normalizar"""
    prob_raw = [1/o for o in odds]
    total_prob = sum(prob_raw)
    factor_normalizacion = total_colocados / total_prob
    prob_ajustada = [p * factor_normalizacion for p in prob_raw]
    return prob_ajustada

def calcular_stakes_optimos(odds, excluir_idx, bankroll=100, total_colocados=2):
    """Calcular stakes óptimos considerando el riesgo"""
    n_perros = len(odds)
    perros_lay = [i for i in range(n_perros) if i != excluir_idx]
    
    # Calcular stakes proporcionales al riesgo
    stakes = []
    for perro in perros_lay:
        # Stake inversamente proporcional a (odds-1) - mayor riesgo, menor stake
        stake_base = bankroll / (odds[perro] - 0.5)
        stakes.append(stake_base)
    
    # Normalizar para que sumen el bankroll deseado
    total_stakes = sum(stakes)
    stakes = [s * bankroll / total_stakes for s in stakes]
    
    return dict(zip(perros_lay, stakes))

def analizar_escenario_completo(odds, excluir_idx, bankroll=100, total_colocados=2):
    """Analizar completamente un escenario de exclusión"""
    prob_ajustada = calcular_probabilidades(odds, total_colocados)
    n_perros = len(odds)
    perros_lay = [i for i in range(n_perros) if i != excluir_idx]
    stakes = calcular_stakes_optimos(odds, excluir_idx, bankroll, total_colocados)
    
    escenarios = []
    ev_total = 0
    
    # Generar todas las combinaciones de perros colocados
    for colocados in combinations(range(n_perros), total_colocados):
        resultado_total = 0
        detalle_stakes = {}
        
        for perro in perros_lay:
            stake = stakes[perro]
            if perro in colocados:
                # Pierdes el lay: pagas (odds[perro] - 1) * stake
                perdida = (odds[perro] - 1) * stake
                resultado_total -= perdida
                detalle_stakes[perro+1] = f"-{perdida:.1f}"
            else:
                # Ganas el lay: ganas stake
                resultado_total += stake
                detalle_stakes[perro+1] = f"+{stake:.1f}"
        
        # Calcular probabilidad de esta combinación (aproximada)
        prob_combinacion = 1.0
        temp_prob = prob_ajustada.copy()
        
        for i, perro in enumerate(colocados):
            if i == 0:
                prob_combinacion *= temp_prob[perro]
            else:
                # Probabilidad condicional simplificada
                prob_restante = total_colocados - i
                prob_combinacion *= (temp_prob[perro] / sum(temp_prob))
        
        contribucion_ev = resultado_total * prob_combinacion
        ev_total += contribucion_ev
        
        escenarios.append({
            'Perros_Colocados': ' y '.join(str(c+1) for c in colocados),
            'Probabilidad': prob_combinacion,
            'Resultado_Total': resultado_total,
            'Contribucion_EV': contribucion_ev,
            **detalle_stakes
        })
    
    return {
        'ev_total': ev_total,
        'stakes': stakes,
        'escenarios': pd.DataFrame(escenarios)
    }

# Configuración de la aplicación
st.set_page_config(page_title="Análisis Lay Galgos", layout="wide")
st.title("📊 Analizador Completo de Estrategia Lay")
st.markdown("**Estrategia**: Lay a N-1 galgos - Stake Óptimo y Análisis por Escenario")

# Entrada de datos flexible
st.header("🎯 Configuración Flexible")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Parámetros de la Carrera")
    n_competidores = st.number_input("Número de competidores", min_value=3, max_value=8, value=6, step=1)
    total_colocados = st.number_input("Número que se colocan", min_value=1, max_value=n_competidores-1, value=2, step=1)
    bankroll = st.number_input("Bankroll Total", min_value=10, value=100, step=10)

with col2:
    st.subheader("Odds de los Competidores")
    st.markdown(f"Ingresa las odds para los {n_competidores} competidores:")
    
    odds = []
    default_odds = [1.64, 2.28, 2.68, 7.8, 36.0, 2.24, 4.0, 5.0]  # Extendido para hasta 8
    
    for i in range(n_competidores):
        odds.append(st.number_input(f"Box {i+1}", min_value=1.01, 
                                  value=default_odds[i], 
                                  step=0.01, key=f"odds_{i}"))

# Selección de análisis
st.subheader("🔍 Tipo de Análisis")
analisis_tipo = st.radio("Selecciona el tipo de análisis:", 
                         ["Comparar todas las exclusiones", "Análisis detallado de una exclusión"])

if analisis_tipo == "Análisis detallado de una exclusión":
    excluir_especifico = st.selectbox("Excluir Box:", 
                                     [f"Box {i+1}" for i in range(n_competidores)])
else:
    excluir_especifico = None

if st.button("🔍 Calcular Análisis Completo"):
    # Validación
    if total_colocados >= n_competidores:
        st.error("❌ El número de colocados debe ser menor que el número de competidores")
        st.stop()
    
    # Análisis general de todos los escenarios
    st.header("📈 Resumen General - Comparación de Estrategias")
    
    resultados_generales = []
    for excluir in range(n_competidores):
        analisis = analizar_escenario_completo(odds, excluir, bankroll, total_colocados)
        stakes = analisis['stakes']
        
        resultado = {
            'Excluir_Box': excluir + 1,
            'Odds_Excluido': odds[excluir],
            'EV_Total': analisis['ev_total'],
            'ROI': (analisis['ev_total'] / bankroll) * 100,
            'Stake_Total': sum(stakes.values())
        }
        
        # Agregar stakes individuales
        for perro, stake in stakes.items():
            resultado[f'Stake_Box_{perro+1}'] = stake
        
        resultados_generales.append(resultado)
    
    df_general = pd.DataFrame(resultados_generales)
    df_general['EV_Total'] = df_general['EV_Total'].round(2)
    df_general['ROI'] = df_general['ROI'].round(2)
    
    # Resaltar mejor estrategia
    def highlight_max(s):
        is_max = s == s.max()
        return ['background-color: #90EE90' if v else '' for v in is_max]
    
    st.dataframe(df_general.style.apply(highlight_max, subset=['EV_Total']), 
                use_container_width=True)
    
    # Mostrar mejor estrategia
    mejor_idx = df_general['EV_Total'].idxmax()
    mejor_box = int(df_general.loc[mejor_idx, 'Excluir_Box'])
    st.success(f"✅ **Mejor estrategia**: Excluir Box {mejor_box} - EV: {df_general.loc[mejor_idx, 'EV_Total']:.2f} (ROI: {df_general.loc[mejor_idx, 'ROI']:.2f}%)")
    
    # Análisis detallado
    st.header("📊 Análisis Detallado")
    
    if analisis_tipo == "Comparar todas las exclusiones":
        # Mostrar todos los escenarios en tabs
        tabs = st.tabs([f"Excluir Box {i+1}" for i in range(n_competidores)])
        
        for i, tab in enumerate(tabs):
            with tab:
                analisis = analizar_escenario_completo(odds, i, bankroll, total_colocados)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(f"💰 Stakes Recomendados")
                    stakes_df = pd.DataFrame([
                        {'Box': perro+1, 'Stake': stake, 'Odds': odds[perro]}
                        for perro, stake in analisis['stakes'].items()
                    ])
                    stakes_df['Stake'] = stakes_df['Stake'].round(2)
                    st.dataframe(stakes_df, use_container_width=True)
                
                with col2:
                    st.subheader("📈 Métricas")
                    ev = analisis['ev_total']
                    roi = (ev / bankroll) * 100
                    st.metric("EV Total", f"{ev:.2f}")
                    st.metric("ROI", f"{roi:.2f}%")
                    st.metric("Número de Escenarios", len(analisis['escenarios']))
                
                st.subheader(f"🎯 Escenarios Posibles ({len(analisis['escenarios'])} combinaciones)")
                df_escenarios = analisis['escenarios']
                df_escenarios['Probabilidad'] = (df_escenarios['Probabilidad'] * 100).round(2)
                df_escenarios['Resultado_Total'] = df_escenarios['Resultado_Total'].round(2)
                df_escenarios['Contribucion_EV'] = df_escenarios['Contribucion_EV'].round(2)
                
                st.dataframe(df_escenarios, use_container_width=True)
    
    else:
        # Mostrar solo el escenario específico seleccionado
        excluir_idx = int(excluir_especifico.split(" ")[1]) - 1
        analisis = analizar_escenario_completo(odds, excluir_idx, bankroll, total_colocados)
        
        st.subheader(f"📋 Resumen - Excluyendo Box {excluir_idx + 1}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Stakes Recomendados")
            stakes_df = pd.DataFrame([
                {'Box': perro+1, 'Stake': stake, 'Odds': odds[perro], 'Riesgo_Max': (odds[perro]-1)*stake}
                for perro, stake in analisis['stakes'].items()
            ])
            stakes_df['Stake'] = stakes_df['Stake'].round(2)
            stakes_df['Riesgo_Max'] = stakes_df['Riesgo_Max'].round(2)
            st.dataframe(stakes_df, use_container_width=True)
            
            total_stake = stakes_df['Stake'].sum()
            max_riesgo = stakes_df['Riesgo_Max'].max()
            st.info(f"**Total Stake:** {total_stake:.2f} | **Máximo Riesgo Individual:** {max_riesgo:.2f}")
        
        with col2:
            st.subheader("📈 Métricas Clave")
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.metric("EV Total", f"{analisis['ev_total']:.2f}")
                st.metric("ROI", f"{(analisis['ev_total']/bankroll)*100:.2f}%")
            with col2_2:
                st.metric("Peor Escenario", 
                         f"{analisis['escenarios']['Resultado_Total'].min():.2f}")
                st.metric("Mejor Escenario", 
                         f"{analisis['escenarios']['Resultado_Total'].max():.2f}")
            st.metric("Número de Escenarios", len(analisis['escenarios']))
        
        st.subheader("🎯 Detalle de Todos los Escenarios")
        df_escenarios = analisis['escenarios']
        df_escenarios['Probabilidad'] = (df_escenarios['Probabilidad'] * 100).round(2)
        df_escenarios['Resultado_Total'] = df_escenarios['Resultado_Total'].round(2)
        df_escenarios['Contribucion_EV'] = df_escenarios['Contribucion_EV'].round(2)
        
        # Ordenar por resultado
        df_escenarios = df_escenarios.sort_values('Resultado_Total', ascending=False)
        st.dataframe(df_escenarios, use_container_width=True)

# Información adicional
with st.expander("💡 Cómo usar la aplicación"):
    st.markdown(f"""
    **Instrucciones:**
    1. **Configura la carrera**: Número de competidores y cuántos se colocan
    2. **Ingresa las odds** de cada competidor
    3. **Selecciona el tipo de análisis**: Comparar todos o ver uno específico
    4. **Revisa los resultados**: EV, stakes recomendados y escenarios
    
    **Ejemplo para carreras con menos competidores:**
    - Carrera con 5 galgos, 2 colocados → Lay a 4 galgos
    - Carrera con 4 galgos, 1 colocado → Lay a 3 galgos
    - Carrera con 8 galgos, 3 colocados → Lay a 7 galgos
    
    **Fórmula general:** Lay a (N-1) galgos, donde N = total de competidores
    """)
