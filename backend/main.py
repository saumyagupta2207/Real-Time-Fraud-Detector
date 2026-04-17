from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, create_model
import xgboost as xgb
import pandas as pd

# 1. INITIALIZE APP & LOAD THE BRAIN
app = FastAPI(title="Real-Time Fraud API", version="1.0")

model = xgb.XGBClassifier()
model.load_model("xgb_fraud_model.json")

# THE SENIOR FIX: Hardcode the schema instead of using brittle pickle files.
# This generates ['V1', 'V2', ... 'V28', 'Amount', 'time_since_last_tx', 'tx_sum_last_12h']
feature_columns = [f"V{i}" for i in range(1, 29)] + ["Amount", "time_since_last_tx", "tx_sum_last_12h"]

# 2. STRICT DATA CONTRACT (Pydantic)
fields = {col: (float, ...) for col in feature_columns}
TransactionInput = create_model('TransactionInput', **fields)

# 3. THE DRIVE-THRU WINDOW (ENDPOINT)
@app.post("/predict")
def predict_fraud(transaction: TransactionInput):
    try:
        input_data = pd.DataFrame([transaction.model_dump()])
        
        # Security/Stability Check: Enforce the exact column order
        input_data = input_data[feature_columns]
        
        probability = float(model.predict_proba(input_data)[0][1])
        is_fraud = bool(probability > 0.85)
        
        return {
            "status": "success",
            "fraud_probability": round(probability, 4),
            "alert_triggered": is_fraud,
            "message": "Transaction blocked." if is_fraud else "Transaction approved."
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
