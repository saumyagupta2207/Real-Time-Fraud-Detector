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
# We now decouple the UI display memory from the background storage memory
if 'display_history' not in st.session_state:
    st.session_state.display_history = []
if 'full_history' not in st.session_state:
    st.session_state.full_history = []
if 'stream_active' not in st.session_state:
    st.session_state.stream_active = False
if 'total_processed' not in st.session_state:
    st.session_state.total_processed = 0
if 'total_anomalies' not in st.session_state:
    st.session_state.total_anomalies = 0

# 2. SYNTHETIC STREAM GENERATOR
def generate_stream_event():
    is_attack = (np.random.random() < 0.15) 
    
    if is_attack:
        payload = {f"V{i}": float(np.random.normal(-8.0, 1.5)) for i in range(1, 29)}
        payload["Amount"] = float(np.random.uniform(15000, 50000))
        payload["time_since_last_tx"] = float(np.random.uniform(0, 2)) 
        payload["tx_sum_last_12h"] = payload["Amount"] + float(np.random.uniform(5000, 10000))
    else:
        payload = {f"V{i}": float(np.random.normal(0, 1)) for i in range(1, 29)}
        payload["Amount"] = float(np.random.uniform(10, 150))
        payload["time_since_last_tx"] = float(np.random.uniform(3600, 86400))
        payload["tx_sum_last_12h"] = payload["Amount"] + float(np.random.uniform(0, 100))
        
    return payload, is_attack

# 3. SIDEBAR: MODEL CARD & EXPORT
with st.sidebar:
    st.header("🧠 Model Card")
    st.markdown("Engine performance metrics based on initial test evaluation.")
    st.metric("Recall (Fraud Caught)", "88.0%")
    st.metric("Precision (Alert Accuracy)", "44.0%")
    st.metric("F1-Score", "0.58")
    st.metric("Accuracy", "99.8%")
    
    st.markdown("---")
    st.header("📥 Data Export")
    st.markdown("Export the complete session history. **Note: You must click 'Stop Stream' before downloading.**")
    
    # Generate the CSV from the full, untruncated history
    if st.session_state.full_history:
        df_full = pd.DataFrame(st.session_state.full_history)
        csv = df_full.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Full CSV Log",
            data=csv,
            file_name=f"fraud_session_log_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

# 4. TOP NAVIGATION & KPIs
st.title("Fraud Detection System")
st.markdown("Autonomous behavioral sequence detection streaming from the XGBoost API.")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("▶️ Start Live Stream", type="primary", use_container_width=True):
        st.session_state.stream_active = True
with col2:
    if st.button("⏹️ Stop Stream", use_container_width=True):
        st.session_state.stream_active = False
with col3:
    # THE NEW RESET BUTTON
    if st.button("🔄 Reset Dashboard", use_container_width=True):
        st.session_state.stream_active = False
        st.session_state.tx_history = []
        st.session_state.full_history = []
        st.session_state.total_processed = 0
        st.session_state.total_anomalies = 0
        st.rerun() # Forces the UI to refresh immediately
with col4:
    metric_anomalies = st.empty()

metric_processed.metric("Transactions Processed", st.session_state.total_processed)
metric_anomalies.metric("Anomalies Intercepted", st.session_state.total_anomalies)

st.markdown("---")

# 5. DASHBOARD LAYOUT
feed_col, alert_col = st.columns([2, 1])

with feed_col:
    st.subheader("Live Transaction Feed")
    feed_placeholder = st.empty()

with alert_col:
    st.subheader("Critical Threat Intelligence")
    alert_placeholder = st.empty()

# 6. THE LIVE STREAM LOOP
if st.session_state.stream_active:
    while st.session_state.stream_active:
        payload, actual_attack = generate_stream_event()
        
        try:
            res = requests.post(API_URL, json=payload).json()
            
            st.session_state.total_processed += 1
            if res.get('alert_triggered'):
                st.session_state.total_anomalies += 1
                
            metric_processed.metric("Transactions Processed", st.session_state.total_processed)
            metric_anomalies.metric("Anomalies Intercepted", st.session_state.total_anomalies)
            
            log_entry = {
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Amount": f"${payload['Amount']:.2f}",
                "Time Delta (s)": f"{payload['time_since_last_tx']:.0f}",
                "Risk Score": f"{res.get('fraud_probability', 0) * 100:.1f}%",
                "Status": "BLOCKED" if res.get('alert_triggered') else "APPROVED"
            }
            
            # Store in the full history for downloading
            st.session_state.full_history.insert(0, log_entry)
            
            # Store in the display history and truncate for UI cleanliness
            st.session_state.display_history.insert(0, log_entry)
            st.session_state.display_history = st.session_state.display_history[:15]
            
            df_display = pd.DataFrame(st.session_state.display_history)
            
            def style_status(row):
                color = '#ff4b4b' if row['Status'] == 'BLOCKED' else '#00cc66'
                return [f'color: {color}'] * len(row)
            
            feed_placeholder.dataframe(df_display.style.apply(style_status, axis=1), use_container_width=True, hide_index=True)
            
            if res.get('alert_triggered'):
                with alert_placeholder.container():
                    st.error("🚨 **HIGH-RISK SIGNATURE DETECTED**")
                    st.markdown(f"**Amount:** ${payload['Amount']:.2f} | **Risk:** {res.get('fraud_probability')*100:.1f}%")
                    st.markdown("**SHAP Root Cause Analysis:**")
                    for feat, weight in res.get('risk_drivers', {}).items():
                        st.markdown(f"- `{feat}`: +{weight}")
            
        except Exception as e:
            feed_placeholder.error("API Disconnected. Please check connection.")
            st.session_state.stream_active = False
            
        time.sleep(1.5)
