import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime

st.set_page_config(page_title="RiskOps Streaming Dashboard", page_icon="📡", layout="wide")

# --- REPLACE WITH YOUR RENDER API URL ---
API_URL = "https://real-time-fraud-detector.onrender.com/predict"

# 1. INITIALIZE MEMORY (State Management)
if 'tx_history' not in st.session_state:
    st.session_state.tx_history = []
if 'stream_active' not in st.session_state:
    st.session_state.stream_active = False

# 2. SYNTHETIC STREAM GENERATOR
def generate_stream_event(force_attack=False):
    is_attack = force_attack or (np.random.random() < 0.15) 
    
    if is_attack:
        # THE ANOMALY: We skew the PCA vectors negatively to mimic a compromised profile
        payload = {f"V{i}": float(np.random.normal(-4.5, 2)) for i in range(1, 29)}
        
        # High velocity, unusual amounts
        payload["Amount"] = float(np.random.uniform(3000, 15000))
        payload["time_since_last_tx"] = float(np.random.uniform(1, 5)) 
        payload["tx_sum_last_12h"] = payload["Amount"] + float(np.random.uniform(100, 500))
    else:
        # Normal baseline profile
        payload = {f"V{i}": float(np.random.normal(0, 1)) for i in range(1, 29)}
        
        # Standard velocity
        payload["Amount"] = float(np.random.uniform(10, 150))
        payload["time_since_last_tx"] = float(np.random.uniform(3600, 86400))
        payload["tx_sum_last_12h"] = payload["Amount"] + float(np.random.uniform(0, 100))
        
    return payload, is_attack
    
# 3. TOP NAVIGATION & KPIs
st.title("📡 Live Cross-Border Fraud Monitor")
st.markdown("Autonomous behavioral sequence detection streaming from the XGBoost API.")

col1, col2, col3, col4 = st.columns(4)

# Stream Controls
with col1:
    if st.button("▶️ Start Live Stream", type="primary", use_container_width=True):
        st.session_state.stream_active = True
with col2:
    if st.button("⏹️ Stop Stream", use_container_width=True):
        st.session_state.stream_active = False
        
with col3:
    st.metric("Transactions Processed", len(st.session_state.tx_history))
with col4:
    fraud_count = sum(1 for tx in st.session_state.tx_history if tx['Status'] == 'BLOCKED')
    st.metric("Anomalies Intercepted", fraud_count)

st.markdown("---")

# 4. DASHBOARD LAYOUT
feed_col, alert_col = st.columns([2, 1])

with feed_col:
    st.subheader("Live Transaction Feed")
    feed_placeholder = st.empty() # Placeholder for our auto-updating table

with alert_col:
    st.subheader("Critical Threat Intelligence")
    alert_placeholder = st.empty() # Placeholder for SHAP explainability

# 5. THE LIVE STREAM LOOP
if st.session_state.stream_active:
    while st.session_state.stream_active:
        # Generate data and hit the API
        payload, actual_attack = generate_stream_event()
        
        try:
            res = requests.post(API_URL, json=payload).json()
            
            # Format the log entry
            log_entry = {
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Amount": f"${payload['Amount']:.2f}",
                "Time Delta (s)": f"{payload['time_since_last_tx']:.0f}",
                "Risk Score": f"{res.get('fraud_probability', 0) * 100:.1f}%",
                "Status": "BLOCKED" if res.get('alert_triggered') else "APPROVED"
            }
            
            # Add to memory (keep only last 15 rows for UI cleanliness)
            st.session_state.tx_history.insert(0, log_entry)
            st.session_state.tx_history = st.session_state.tx_history[:15]
            
            # --- UPDATE THE UI ---
            df = pd.DataFrame(st.session_state.tx_history)
            
            # Color code the dataframe based on status
            def style_status(row):
                color = '#ff4b4b' if row['Status'] == 'BLOCKED' else '#00cc66'
                return [f'color: {color}'] * len(row)
            
            feed_placeholder.dataframe(df.style.apply(style_status, axis=1), use_container_width=True, hide_index=True)
            
            # Update the Alert Panel if a threat is caught
            if res.get('alert_triggered'):
                with alert_placeholder.container():
                    st.error("🚨 **HIGH-RISK SIGNATURE DETECTED**")
                    st.markdown(f"**Amount:** ${payload['Amount']:.2f} | **Risk:** {res.get('fraud_probability')*100:.1f}%")
                    st.markdown("**SHAP Root Cause Analysis:**")
                    for feat, weight in res.get('risk_drivers', {}).items():
                        st.markdown(f"- `{feat}`: +{weight}")
            
        except Exception as e:
            feed_placeholder.error("API Disconnected.")
            st.session_state.stream_active = False
            
        # Pause for 1.5 seconds before the next transaction hits
        time.sleep(1.5)
