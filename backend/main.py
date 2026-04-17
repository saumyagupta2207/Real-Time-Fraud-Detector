from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, create_model
import xgboost as xgb
import pandas as pd
import shap
import numpy as np

# 1. INITIALIZE APP & LOAD THE BRAIN
app = FastAPI(title="Real-Time Fraud API", version="1.2")

model = xgb.XGBClassifier()
model.load_model("xgb_fraud_model.json")
explainer = shap.TreeExplainer(model)

feature_columns = [f"V{i}" for i in range(1, 29)] + ["Amount", "time_since_last_tx", "tx_sum_last_12h"]

# 2. STRICT DATA CONTRACT
fields = {col: (float, ...) for col in feature_columns}
TransactionInput = create_model('TransactionInput', **fields)

# 3. THE ENDPOINT (Pure Math, No Business Logic)
@app.post("/predict")
def predict_fraud(transaction: TransactionInput):
    try:
        input_data = pd.DataFrame([transaction.model_dump()])[feature_columns]
        
        # 1. Calculate raw probability
        probability = float(model.predict_proba(input_data)[0][1])
        
        # 2. Calculate SHAP values for Explainability every single time
        shap_values = explainer.shap_values(input_data)
        feature_impact = {col: float(val) for col, val in zip(feature_columns, shap_values[0])}
        
        # 3. Extract the top 3 risk drivers
        top_risk_drivers = {k: round(v, 4) for k, v in sorted(feature_impact.items(), key=lambda item: item[1], reverse=True)[:3] if v > 0}
        
        # 4. Return pure data. Let the frontend decide what to do with it.
        return {
            "status": "success",
            "fraud_probability": round(probability, 4),
            "risk_drivers": top_risk_drivers
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
