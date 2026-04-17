import streamlit as st
import requests
import time
import pandas as pd
import numpy as np

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Fraud Risk Command Center", page_icon="🛡️", layout="wide")
st.title("🛡️ Real-Time Fraud Command Center")

# --- REPLACE THIS WITH YOUR RENDER API URL ---
# Make sure it ends with /predict
API_URL = "https://real-time-fraud-detector.onrender.com/predict"

# 2. SIMULATION DATA GENERATOR
# Since the actual bank data is massive, we generate synthetic payloads 
# that mimic the 30+ columns the XGBoost model expects.
def generate_synthetic_payload(is_attack=False):
    # V1-V28 are PCA transformed features from the original Kaggle dataset
    payload = {f"V{i}": np.random.normal(0, 1) for i in range(1, 29)}
    
    if is_attack:
        # Attack Sequence: High velocity, unusual amounts, tiny time delta
        payload["Amount"] = np.random.uniform(5000, 10000)
        payload["time_since_last_tx"] = np.random.uniform(1, 10) # 1 to 10 seconds ago!
        payload["tx_sum_last_12h"] = payload["Amount"] * np.random.uniform(4, 10)
    else:
        # Normal Behavior: Standard amounts, normal time deltas
        payload["Amount"] = np.random.uniform(5, 100)
        payload["time_since_last_tx"] = np.random.uniform(3600, 86400) # Hours/Days ago
        payload["tx_sum_last_12h"] = payload["Amount"] * np.random.uniform(1, 2)
        
    return payload

# 3. UI DASHBOARD LAYOUT
st.markdown("### 📡 Live Transaction Feed")
col1, col2 = st.columns([2, 1])

with col1:
    st.write("Control Panel")
    btn_normal = st.button("✅ Simulate Normal Transaction", use_container_width=True)
    btn_attack = st.button("🚨 Simulate Velocity Attack", type="primary", use_container_width=True)

with col2:
    st.write("System Status")
    if st.button("Ping API Server"):
        try:
            # We hit the root endpoint just to wake up the server
            res = requests.get(API_URL.replace("/predict", ""))
            st.success("API is Online and Connected.")
        except:
            st.error("Cannot reach API. Check URL.")

# 4. EXECUTION LOGIC
st.markdown("---")
st.subheader("Transaction Analysis Log")

if btn_normal or btn_attack:
    payload = generate_synthetic_payload(is_attack=btn_attack)
    
    with st.spinner("Analyzing cross-border behavioral sequence..."):
        try:
            # Send the JSON payload to your FastAPI drive-thru window
            response = requests.post(API_URL, json=payload)
            
            # THE SENIOR FIX: Catch API rejections before parsing the math
            if response.status_code != 200:
                st.error(f"Backend API Error (Code {response.status_code})")
                st.json(response.json()) # Print the exact error Render is throwing
            else:
                result = response.json()
                
                # Display results
                if result.get("alert_triggered"):
                    st.error(f"🛑 THREAT DETECTED: {result.get('message')}")
                    st.metric(label="Fraud Probability Confidence", value=f"{result.get('fraud_probability') * 100:.2f}%")
                    st.json(payload)
                else:
                    st.success(f"✅ CLEAR: {result.get('message')}")
                    st.metric(label="Fraud Probability Confidence", value=f"{result.get('fraud_probability') * 100:.2f}%")
                    
        except Exception as e:
            st.error(f"Frontend Request Failed: {e}")
