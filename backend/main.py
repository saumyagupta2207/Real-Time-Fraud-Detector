from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, create_model
import xgboost as xgb
import pandas as pd
import joblib

# 1. INITIALIZE APP & LOAD THE BRAIN (GLOBAL SCOPE)
# We load the model outside the endpoint so it only loads once when the server boots.
# If we put this inside the /predict function, the server would read the hard drive 
# on every single transaction, destroying our real-time latency.
app = FastAPI(title="Real-Time Fraud API", version="1.0")

model = xgb.XGBClassifier()
model.load_model("xgb_fraud_model.json")
feature_columns = joblib.load("feature_columns.pkl") 

# 2. STRICT DATA CONTRACT (Pydantic)
# We dynamically build a schema expecting exactly the columns our model was trained on.
fields = {col: (float, ...) for col in feature_columns}
TransactionInput = create_model('TransactionInput', **fields)

# 3. THE DRIVE-THRU WINDOW (ENDPOINT)
@app.post("/predict")
def predict_fraud(transaction: TransactionInput):
    try:
        # Convert incoming JSON payload to a one-row Pandas DataFrame
        # .model_dump() is the modern Pydantic way to extract the dictionary
        input_data = pd.DataFrame([transaction.model_dump()])
        
        # Security/Stability Check: Enforce the exact column order the model expects
        input_data = input_data[feature_columns]
        
        # Get probability (predict_proba returns [[prob_normal, prob_fraud]])
        probability = float(model.predict_proba(input_data)[0][1])
        
        # Business Logic: Threshold set at 85% confidence
        is_fraud = bool(probability > 0.85)
        
        return {
            "status": "success",
            "fraud_probability": round(probability, 4),
            "alert_triggered": is_fraud,
            "message": "Transaction blocked." if is_fraud else "Transaction approved."
        }
        
    except Exception as e:
        # Never fail silently. Return a clean 400 Bad Request error.
        raise HTTPException(status_code=400, detail=str(e))
