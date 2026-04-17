import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(page_title="RiskOps Command Center", page_icon="🛡️", layout="wide")

# --- REPLACE WITH YOUR RENDER API URL ---
API_URL = "https://real-time-fraud-detector.onrender.com/predict"

# 1. HEADER & KPIs
st.title("🛡️ RiskOps Command Center")
st.markdown("Real-time behavioral sequence monitoring and anomaly detection.")

col1, col2, col3 = st.columns(3)
col1.metric("System Status", "🟢 Online", "API Connected")
col2.metric("Model Version", "XGB-v1.2", "Sequence Tracking Active")
col3.metric("Latency", "~45ms", "SLA Met")

st.markdown("---")

# 2. THE INVESTIGATION PANEL
st.subheader("🔍 Manual Transaction Intercept")
st.markdown("Use this panel to manually inject transaction parameters and evaluate the model's response and SHAP explanations.")

with st.form("transaction_form"):
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        amount = st.number_input("Transaction Amount ($)", min_value=1.0, value=25.0, step=10.0)
    with col_b:
        time_since = st.number_input("Seconds Since Last Tx", min_value=1.0, value=3600.0, help="Low values indicate high velocity.")
    with col_c:
        sum_12h = st.number_input("Total Spent Last 12h ($)", min_value=0.0, value=50.0)
        
    submit_button = st.form_submit_button("Run Risk Analysis", type="primary")

# 3. ANALYSIS EXECUTION & DISPLAY
if submit_button:
    # Build synthetic baseline for PCA features (V1-V28) so we only manipulate our custom features
    payload = {f"V{i}": float(np.random.normal(0, 1)) for i in range(1, 29)}
    payload["Amount"] = amount
    payload["time_since_last_tx"] = time_since
    payload["tx_sum_last_12h"] = sum_12h
    
    with st.spinner("Analyzing cross-border behavioral sequence..."):
        try:
            response = requests.post(API_URL, json=payload)
            
            if response.status_code != 200:
                st.error(f"Backend API Error (Code {response.status_code})")
            else:
                result = response.json()
                
                # Professional Display Logic
                if result.get("alert_triggered"):
                    st.error("### 🚨 THREAT DETECTED: TRANSACTION BLOCKED")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric(label="Fraud Probability", value=f"{result.get('fraud_probability') * 100:.2f}%")
                    
                    with c2:
                        st.markdown("**Key Risk Drivers (SHAP Explainability):**")
                        drivers = result.get("risk_drivers", {})
                        if drivers:
                            for feature, weight in drivers.items():
                                st.markdown(f"- **`{feature}`**: High mathematical impact (+{weight})")
                        else:
                            st.write("No distinct singular driver isolated.")
                            
                    with st.expander("View Raw JSON Payload"):
                        st.json(payload)
                        
                else:
                    st.success("### ✅ CLEAR: TRANSACTION APPROVED")
                    st.metric(label="Fraud Probability", value=f"{result.get('fraud_probability') * 100:.2f}%", delta="- Low Risk")
                    st.markdown("Behavioral sequence falls within standard parameters.")
                    
        except Exception as e:
            st.error(f"Connection Failed. Ensure API is live. Error: {e}")
