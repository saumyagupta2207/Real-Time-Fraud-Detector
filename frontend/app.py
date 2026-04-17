import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Real Time Fraud Detection Dashboard", page_icon="📡", layout="wide")

# --- REPLACE WITH YOUR RENDER API URL ---
API_URL = "https://real-time-fraud-detector.onrender.com/predict"

# 1. INITIALIZE MEMORY (State Management)
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

# 3. SIDEBAR: CONFIG, MODEL CARD & EXPORT
with st.sidebar:
    st.header("⚙️ Risk Configuration")
    risk_threshold = st.slider(
        "Global Block Threshold (%)", 
        min_value=1.0, 
        max_value=99.0, 
        value=85.0, 
        step=1.0,
        help="Transactions with a risk score above this value will be automatically blocked."
    )
    st.markdown("---")
    
    st.header("🧠 Model Card")
    st.markdown("Engine performance metrics based on initial test evaluation.")
    st.metric("Recall (Fraud Caught)", "88.0%")
    st.metric("Precision (Alert Accuracy)", "44.0%")
    st.metric("F1-Score", "0.58")
    st.metric("Accuracy", "99.8%")
    
    st.markdown("---")
    st.header("📥 Data Export")
    st.markdown("Export the complete session history. **Note: You must click 'Stop Stream' before downloading.**")
    
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
st.title("Real Time Fraud Detection System")
st.markdown("Autonomous behavioral sequence detection streaming from the XGBoost API.")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("▶️ Start Live Stream", type="primary", use_container_width=True):
        st.session_state.stream_active = True
with col2:
    if st.button("⏹️ Stop Stream", use_container_width=True):
        st.session_state.stream_active = False
with col3:
    if st.button("🔄 Reset Dashboard", use_container_width=True):
        st.session_state.stream_active = False
        st.session_state.display_history = []
        st.session_state.full_history = []
        st.session_state.total_processed = 0
        st.session_state.total_anomalies = 0
        st.rerun() 
with col4:
    metric_processed = st.empty()
with col5:
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
            
            # --- THE DYNAMIC RULES ENGINE ---
            raw_prob_percent = res.get('fraud_probability', 0) * 100
            
            # The UI decides if it's blocked based on your slider
            is_blocked = bool(raw_prob_percent >= risk_threshold)
            
            st.session_state.total_processed += 1
            if is_blocked:
                st.session_state.total_anomalies += 1
                
            metric_processed.metric("Transactions Processed", st.session_state.total_processed)
            metric_anomalies.metric("Anomalies Intercepted", st.session_state.total_anomalies)
            
            # Calculate exact IST (UTC + 5:30)
            ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
            
            log_entry = {
                "Timestamp": ist_time.strftime("%H:%M:%S"),
                "Amount": f"${payload['Amount']:.2f}",
                "Time Delta (s)": f"{payload['time_since_last_tx']:.0f}",
                "Risk Score": f"{raw_prob_percent:.1f}%",
                "Status": "BLOCKED" if is_blocked else "APPROVED"
            }
            
            st.session_state.full_history.insert(0, log_entry)
            
            st.session_state.display_history.insert(0, log_entry)
            st.session_state.display_history = st.session_state.display_history[:15]
            
            df_display = pd.DataFrame(st.session_state.display_history)
            
            def style_status(row):
                color = '#ff4b4b' if row['Status'] == 'BLOCKED' else '#00cc66'
                return [f'color: {color}'] * len(row)
            
            feed_placeholder.dataframe(df_display.style.apply(style_status, axis=1), use_container_width=True, hide_index=True)
            
            if is_blocked:
                with alert_placeholder.container():
                    st.error("🚨 **HIGH-RISK SIGNATURE DETECTED**")
                    st.markdown(f"**Amount:** ${payload['Amount']:.2f} | **Risk:** {raw_prob_percent:.1f}%")
                    st.markdown("**SHAP Root Cause Analysis:**")
                    for feat, weight in res.get('risk_drivers', {}).items():
                        st.markdown(f"- `{feat}`: +{weight}")
            
        except Exception as e:
            feed_placeholder.error("API Disconnected. Please check connection.")
            st.session_state.stream_active = False
            
        time.sleep(1.5)
