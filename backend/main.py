from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, create_model
import xgboost as xgb
import pandas as pd
import shap
import numpy as np

# 1. INITIALIZE APP & LOAD THE BRAIN
app = FastAPI(title="Real-Time Fraud API", version="1.1")

model = xgb.XGBClassifier()
model.load_model("xgb_fraud_model.json")

# Initialize SHAP explainer globally to prevent latency spikes
explainer = shap.TreeExplainer(model)

feature_columns = [f"V{i}" for i in range(1, 29)] + ["Amount", "time_since_last_tx", "tx_sum_last_12h"]

# 2. STRICT DATA CONTRACT
fields = {col: (float, ...) for col in feature_columns}
TransactionInput = create_model('TransactionInput', **fields)

# 3. THE ENDPOINT
@app.post("/predict")
def predict_fraud(transaction: TransactionInput):
    try:
        input_data = pd.DataFrame([transaction.model_dump()])[feature_columns]
        
        # Get probability
        probability = float(model.predict_proba(input_data)[0][1])
        is_fraud = bool(probability > 0.5)
        
        # Calculate SHAP values for Explainability
        shap_values = explainer.shap_values(input_data)
        
        # Map values to feature names and extract the top 3 risk drivers
        feature_impact = {col: float(val) for col, val in zip(feature_columns, shap_values[0])}
        # Sort by features pushing the fraud score highest
        top_risk_drivers = {k: round(v, 4) for k, v in sorted(feature_impact.items(), key=lambda item: item[1], reverse=True)[:3] if v > 0}
        
        return {
            "status": "success",
            "fraud_probability": round(probability, 4),
            "alert_triggered": is_fraud,
            "message": "Transaction blocked. High risk signature detected." if is_fraud else "Transaction approved.",
            "risk_drivers": top_risk_drivers if is_fraud else {}
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
