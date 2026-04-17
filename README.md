# 🛡️ Real-Time Cross-Border Fraud Anomaly Detection Engine

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25+-FF4B4B.svg?logo=streamlit)](https://streamlit.io/)
[![XGBoost](https://img.shields.io/badge/XGBoost-1.7+-blue.svg)](https://xgboost.readthedocs.io/)

**Live RiskOps Dashboard:** [https://real-time-fraud-detector-saumyahere.streamlit.app/]  
**Live API Endpoint:** [https://real-time-fraud-detector.onrender.com/docs]  

## 🧠 The Business Philosophy: Fraud is a Sequence, Not an Event
Most traditional fraud detection frameworks fail because they evaluate transactions in a vacuum, relying on static rule-based thresholds. In reality, modern fraud follows a geometric progression—a rapid sequence of low-value pings or account testing before the major extraction.

This system takes a **behavioral approach**. By utilizing temporal feature engineering, the engine tracks the "velocity" of a user's financial behavior, connecting signals across time to intercept escalating attacks before the critical hit.

## 🏗️ Enterprise-Grade Architecture
This project implements a decoupled, stateless-backend/stateful-frontend microservice architecture, designed for high-availability production environments.

### 1. The Inference Engine (Stateless Backend)
* **Algorithm:** An XGBoost classifier trained on real-world European fintech data.
* **Framework:** A high-performance REST API built with **FastAPI** and deployed on **Render**.
* **Data Contracts:** Enforces strict payload validation via **Pydantic** to prevent system crashes from malformed, missing, or corrupted upstream data.
* **Real-Time Explainability:** Integrates **SHAP (SHapley Additive exPlanations)** to calculate the exact mathematical weight of every feature on the fly, instantly converting black-box probabilities into actionable business intelligence.

### 2. RiskOps Command Center (Stateful Frontend)
* **Framework:** An autonomous, live-streaming UI built with **Streamlit Community Cloud**.
* **Dynamic Rules Engine:** Moves the business logic to the client side. Risk Managers can dynamically adjust the global block threshold via a slider, allowing the business to balance security and friction without requiring backend redeployments.
* **Live Telemetry:** Features auto-refreshing KPIs, a rolling transaction log, and a decoupled memory state for full-session CSV data exporting.

## 💻 Tech Stack
* **Machine Learning:** `xgboost`, `scikit-learn`, `shap`, `pandas`, `numpy`
* **Backend Engineering:** `FastAPI`, `uvicorn`, `pydantic`
* **Frontend UI:** `Streamlit`, `requests`
* **Cloud Deployment:** `Render` (API), `Streamlit Community Cloud` (Client)

## 🚦 Endpoint Documentation
The API expects a strictly typed JSON payload representing the engineered behavioral features of a transaction.

**Endpoint:** `POST /predict`

**Response Payload Example:**
```json
{
  "status": "success",
  "fraud_probability": 0.9612,
  "risk_drivers": {
    "time_since_last_tx": 4.1201,
    "tx_sum_last_12h": 1.4502,
    "Amount": 0.8931
  }
}
