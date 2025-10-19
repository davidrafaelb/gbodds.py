import streamlit as st
import pandas as pd
import numpy as np

def calcular_valor_y_stakes(win1, win2, place1, place2, commission=0.02):
    """
    Enfoque CORRECTO: calcular valor y ajustar stakes Back primero
    """
    # Probabilidades teóricas (6 galgos iguales)
    prob_teorica_ganar = 1/6
    prob_teorica_colocado = 1/3
    
    # Probabilidades implícitas del mercado
    prob_impl_win1 = 1 / win1
    prob_impl_win2 = 1 / win2
    prob_impl_place1 = 1 / place1
    prob_impl_place2 = 1 / place2
    
    # Calcular VALOR (prob_teorica / prob_implícita)
    valor_win1 = prob_teorica_ganar / prob_impl_win1
    valor_win2 = prob_teorica_ganar / prob_impl_win2
    valor_place1 = prob_teorica_colocado / prob_impl_place1
    valor_place2 = prob_teorica_colocado / prob_impl_place2
    
    # DECIDIR APUESTAS BACK solo si tienen valor
    back_stake1, back_stake2 = 0, 0
    
    if valor_win1 > 1:  # Tiene valor positivo
        back_stake1 = min(valor_win1, 2.0)  # Stake proporcional al valor
    if valor_win2 > 1:
        back_stake2 = min(valor_win2, 2.0)
    
    # Si ninguno tiene valor, usar el menos malo
    if back_stake1 == 0 and back_stake2 == 0:
        if valor_win1 > valor_win2:
            back_stake1 = 1.0
        else:
            back_stake2 = 1.0
    
    return back_stake1, back_stake2, valor_win1, valor_win2

def optimizar_completo(win1, win2, place1, place2, commission=0.02):
    """
    Optimización COMPLETA: valor + stakes Back + stakes Lay
    """
    # 1. Calcular stakes Back basados en valor
    back_stake1, back_stake2, valor1, valor2 = calcular_valor_y_stakes(win1, win2, place1, place2, commission)
    
    # 2. Calcular stakes Lay óptimos para esos stakes Back
    com_factor = 1 - commission
    
    # Estimación simple de stakes Lay
    if back_stake1 > 0 and back_stake2 > 0:
        # Apostando a ambos -> stakes Lay balanceados
        lay_stake1 = 1.5
        lay_stake2 = 1.5
    elif back_stake1 > 0:
        # Solo apostando a G1 -> más Lay en G2
        lay_stake1 = 0.8
        lay_stake2 = 1.8
    else:
        # Solo apostando a G2 -> más Lay en G1  
        lay_stake1 = 1.8
        lay_stake2 = 0.8
    
    return back_stake1, back_stake2, lay_stake1, lay_stake2, valor1, valor2

# INTERFAZ STREAMLIT MEJORADA
st.set_page_config(page_title="Optimizador con Valor", page_icon="🏁", layout="centered")

st.title("🏁 Optimizador CON VALOR Real")

st.info("💰 **Ahora considera VALOR** - Stakes Back proporcionales al valor encontrado")

# Entrada de datos
st.header("📊 Odds de los Galgos")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Galgo 1")
    win1 = st.number_input("Odd a Ganar", value=6.00, min_value=1.0, key="win1")
    place1 = st.number_input("Odd a Colocado", value=2.50, min_value=1.0, key="place1")

with col2:
    st.subheader("Galgo 2")  
    win2 = st.number_input("Odd a Ganar", value=2.00, min_value=1.0, key="win2")
    place2 = st.number_input("Odd a Colocado", value=1.40, min_value=1.0, key="place2")

commission = st.slider("🎯 Comisión del Exchange (%)", 0.0, 10.0, 2.0) / 100

if st.button("🎲 Optimizar con VALOR", type="primary"):
    back_stake1, back_stake2, lay_stake1, lay_stake2, valor1, valor2 = optimizar_completo(win1, win2, place1, place2, commission)
    
    # MOSTRAR ANÁLISIS DE VALOR
    st.header("🔍 Análisis de Valor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Galgo 1")
        st.metric("Odd Ganar", f"{win1:.2f}")
        st.metric("Valor", f"{valor1:.2f}")
        st.metric("Recomendación", "✅ APOSTAR" if valor1 > 1 else "❌ EVITAR")
    
    with col2:
        st.subheader("Galgo 2")
        st.metric("Odd Ganar", f"{win2:.2f}") 
        st.metric("Valor", f"{valor2:.2f}")
        st.metric("Recomendación", "✅ APOSTAR" if valor2 > 1 else "❌ EVITAR")
    
    # ESTRATEGIA FINAL
    st.header("💡 Estrategia Optimizada con VALOR")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Apuestas a Ganador")
        if back_stake1 > 0:
            st.metric("Galgo 1", f"${back_stake1:.2f} @ {win1:.2f}")
        else:
            st.write("Galgo 1: ❌ No apostar")
            
        if back_stake2 > 0:
            st.metric("Galgo 2", f"${back_stake2:.2f} @ {win2:.2f}")
        else:
            st.write("Galgo 2: ❌ No apostar")
    
    with col2:
        st.subheader("Lay a Colocado")
        st.metric("Contra Galgo 1", f"${lay_stake1:.2f}")
        st.metric("Contra Galgo 2", f"${lay_stake2:.2f}")

# EXPLICACIÓN
with st.expander("📚 ¿Cómo se calcula el VALOR?"):
    st.write("""
    **Fórmula de valor:**
    ```
    VALOR = Probabilidad Teórica / Probabilidad Implícita
    ```
    
    **Donde:**
    - Probabilidad Teórica = 16.67% (ganar) o 33.33% (colocado)  
    - Probabilidad Implícita = 1 / Odd
    
    **Interpretación:**
    - VALOR > 1.0 = Buena apuesta ✅
    - VALOR < 1.0 = Mala apuesta ❌
    
    **Ejemplo con odds 6.00 vs 2.00:**
    - Odd 6.00: VALOR = 16.67% / (1/6) = 1.0 → Valor neutral
    - Odd 2.00: VALOR = 16.67% / 50% = 0.33 → Pésimo valor
    """)

st.markdown("---")
st.caption("⚠️ Herramienta educativa - Apueste responsablemente")
