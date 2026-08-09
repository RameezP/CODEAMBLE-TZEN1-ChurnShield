from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import pandas as pd
import numpy as np
import shap
import io
import math
from typing import Optional, List, Dict, Any

from app.model_loader import get_model, get_preprocessor
from app.schemas import CustomerData, RetentionSimulateRequest, AgentChatRequest, StrategyRequest
from app.recommendation_engine import get_risk_level, calculate_financial_exposure, get_retention_recommendations
from app.agent_engine import RetentionAgentOrchestrator, _reverse_onehot_map, to_jsonable_deep
from app.communication_engine import generate_communication

app = FastAPI(
    title="ChurnShield One Multi-Industry API",
    description="Agentic Customer Retention Intelligence API (Telecom, OTT, Banking)",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CommunicationRequest(BaseModel):
    customer_id: Optional[str] = "CUST-001"
    industry: str = Field(default="telecom")
    risk_level: str = Field(default="HIGH")
    churn_probability: float = Field(default=0.75)
    top_drivers: List[Dict[str, Any]] = []
    recommendation: str = Field(default="Offer 15% discount and contract upgrade")
    channel: str = Field(default="email")
    tone: str = Field(default="professional")
    profile: Optional[Dict[str, Any]] = {}

def sanitize_float(val):
    if math.isnan(val) or math.isinf(val):
        return 0.0
    return float(val)

PROFILE_FIELDS = {
    "telecom": [
        "Gender", "Age", "Tenure in Months", "Contract", "Internet Service", "Internet Type",
        "Payment Method", "Monthly Charge", "Total Revenue", "Satisfaction Score",
        "CLTV", "City", "Online Security", "Premium Tech Support", "Number of Referrals"
    ],
    "ott": [
        "Gender", "Age", "Subscription Type", "Monthly Charge", "Tenure Months",
        "Avg Monthly Watch Hours", "Days Since Last Login", "Profile Count",
        "Devices Registered", "Support Tickets"
    ],
    "banking": [
        "Customer_Age", "Gender", "Education_Level", "Marital_Status",
        "Income_Category", "Card_Category", "Months_on_book",
        "Total_Relationship_Count", "Months_Inactive_12_mon",
        "Contacts_Count_12_mon", "Credit_Limit", "Total_Revolving_Bal",
        "Avg_Utilization_Ratio", "Total_Trans_Amt", "Total_Trans_Ct"
    ]
}

def to_jsonable(val):
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating, float)):
        if math.isnan(float(val)) or math.isinf(float(val)):
            return None
        return round(float(val), 4)
    if isinstance(val, np.bool_):
        return bool(val)
    if pd.isna(val):
        return None
    return str(val)

def compute_industry_analytics(df_raw: pd.DataFrame, industry: str) -> dict:
    analytics = {}
    industry = industry.lower()

    def dist(col):
        if col in df_raw.columns:
            return df_raw[col].value_counts().head(8).to_dict()
        return {}

    if industry == "telecom":
        analytics["contract_distribution"] = dist("Contract")
        analytics["internet_type_distribution"] = dist("Internet Type")
        analytics["payment_method_distribution"] = dist("Payment Method")
        if "Monthly Charge" in df_raw.columns:
            analytics["average_monthly_charge"] = round(float(df_raw["Monthly Charge"].mean()), 2)
        if "Satisfaction Score" in df_raw.columns:
            analytics["average_satisfaction"] = round(float(df_raw["Satisfaction Score"].mean()), 2)
        if "Tenure in Months" in df_raw.columns:
            analytics["average_tenure"] = round(float(df_raw["Tenure in Months"].mean()), 2)

    elif industry == "ott":
        analytics["subscription_distribution"] = dist("Subscription Type")
        if "Avg Monthly Watch Hours" in df_raw.columns:
            analytics["average_watch_hours"] = round(float(df_raw["Avg Monthly Watch Hours"].mean()), 2)
        if "Days Since Last Login" in df_raw.columns:
            analytics["average_days_since_login"] = round(float(df_raw["Days Since Last Login"].mean()), 2)
        if "Monthly Charge" in df_raw.columns:
            analytics["average_monthly_charge"] = round(float(df_raw["Monthly Charge"].mean()), 2)

    elif industry == "banking":
        analytics["card_category_distribution"] = dist("Card_Category")
        analytics["income_category_distribution"] = dist("Income_Category")
        if "Avg_Utilization_Ratio" in df_raw.columns:
            analytics["average_utilization_ratio"] = round(float(df_raw["Avg_Utilization_Ratio"].mean()), 4)
        if "Total_Trans_Ct" in df_raw.columns:
            analytics["average_transaction_count"] = round(float(df_raw["Total_Trans_Ct"].mean()), 2)
        if "Months_Inactive_12_mon" in df_raw.columns:
            analytics["average_inactive_months"] = round(float(df_raw["Months_Inactive_12_mon"].mean()), 2)
        if "Credit_Limit" in df_raw.columns:
            analytics["average_credit_limit"] = round(float(df_raw["Credit_Limit"].mean()), 2)

    return analytics

@app.get("/")
def health_check():
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    return {
        "status": "online",
        "platform": "ChurnShield One",
        "supported_industries": ["telecom", "ott", "banking"],
        "llm": {
            "provider": "google",
            "configured": bool(gemini_key and not gemini_key.startswith("csk-")),
            "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        }
    }

@app.post("/predict")
def predict_churn(payload: CustomerData):
    industry = payload.industry.lower()
    orchestrator = RetentionAgentOrchestrator(industry)
    res = orchestrator.run_pipeline(payload.data, payload.customer_id or "CUST-001")
    return to_jsonable_deep(res)

@app.post("/bulk_predict")
async def bulk_predict(file: UploadFile = File(...), industry: str = Form("telecom")):
    industry = industry.lower()
    
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV dataset.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty.")

    try:
        df_raw = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV structure: {str(e)}")

    df_raw = df_raw.loc[:, ~df_raw.columns.str.contains('^Unnamed')]

    if "CLIENTNUM" in df_raw.columns and "Customer ID" not in df_raw.columns:
        df_raw["Customer ID"] = df_raw["CLIENTNUM"]

    customer_ids = df_raw["Customer ID"].astype(str).tolist() if "Customer ID" in df_raw.columns else [f"CUST-{i+1}" for i in range(len(df_raw))]

    drop_cols = ["Customer ID", "CLIENTNUM", "Churn", "Attrition_Flag", "Customer Status", "Churn Category", "Churn Reason", "Lat Long", "Churn Score"]
    df_features = df_raw.drop(columns=drop_cols, errors="ignore")

    model = get_model(industry)
    preprocessor = get_preprocessor(industry)

    num_cols = list(preprocessor.transformers_[0][2])
    cat_cols = list(preprocessor.transformers_[1][2])
    expected_cols = num_cols + cat_cols
    for col in expected_cols:
        if col not in df_features.columns:
            df_features[col] = np.nan

    try:
        processed = preprocessor.transform(df_features)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Dataset columns do not match expected features for '{industry}': {str(e)}")

    if hasattr(processed, "toarray"):
        processed_dense = processed.toarray()
    else:
        processed_dense = processed

    preds = model.predict(processed_dense)
    probs = model.predict_proba(processed_dense)[:, 1]

    feature_names = None
    try:
        num_cols = list(preprocessor.transformers_[0][2])
        cat_cols = list(preprocessor.transformers_[1][2])
        cat_encoder = preprocessor.named_transformers_["cat"].named_steps["encoder"]
        cat_feature_names = cat_encoder.get_feature_names_out(cat_cols).tolist() if cat_cols else []
        feature_names = num_cols + cat_feature_names
    except Exception:
        feature_names = None

    explainer = None
    shap_matrix = None
    if feature_names is not None:
        try:
            explainer = shap.TreeExplainer(model)
            raw_shap = explainer.shap_values(processed_dense)
            if isinstance(raw_shap, list):
                shap_matrix = np.asarray(raw_shap[1] if len(raw_shap) > 1 else raw_shap[0])
            else:
                shap_matrix = np.asarray(raw_shap)
        except Exception:
            shap_matrix = None

    results = []
    risk_summary = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    total_exposure = 0.0
    profile_fields = PROFILE_FIELDS.get(industry, [])
    at_risk = 0

    for i in range(len(df_raw)):
        prob = sanitize_float(probs[i])
        pred = int(preds[i])
        r_level = get_risk_level(prob)
        risk_summary[r_level] += 1
        if r_level in ("HIGH", "CRITICAL"):
            at_risk += 1

        cust_row = df_raw.iloc[i].to_dict()
        exposure = calculate_financial_exposure(cust_row, prob, industry)
        
        primary_loss = exposure.get("risk_revenue_loss", exposure.get("transaction_volume_at_risk", 0.0))
        total_exposure += primary_loss

        profile = {}
        for field in profile_fields:
            if field in cust_row:
                profile[field] = to_jsonable(cust_row[field])

        GEO_IGNORE = {"city", "zip code", "latitude", "longitude", "lat long", "lat_long"}
        shap_drivers = []
        if shap_matrix is not None and feature_names is not None:
            try:
                row_vals = shap_matrix[i]
                if hasattr(row_vals, "flatten"):
                    row_vals = row_vals.flatten()
                abs_vals = np.abs(row_vals)
                idx_sorted = np.argsort(-abs_vals)  # sort by abs descending

                # Collect top 10 non-geo features first, then compute relative importance
                top_entries = []
                for j in idx_sorted:
                    fname = feature_names[j]
                    if any(g in fname.lower() for g in GEO_IGNORE):
                        continue
                    shap_val = sanitize_float(row_vals[j])
                    abs_shap = abs(shap_val)

                    # FIX #2 — accurate one-hot reverse mapping
                    original_attr, feat_val = _reverse_onehot_map(fname, cust_row)

                    top_entries.append({
                        "feature":       original_attr,
                        "raw_feature":   fname,
                        "impact":        shap_val,
                        "abs_impact":    round(abs_shap, 4),
                        # FIX #1 — direction determined ONLY by SHAP sign
                        "direction":     "churn" if shap_val > 0 else "retention",
                        "feature_value": feat_val
                    })
                    if len(top_entries) >= 10:
                        break

                # FIX #5 — compute relative importance % across top-N
                total_abs = sum(e["abs_impact"] for e in top_entries)
                for entry in top_entries:
                    entry["importance"] = round(
                        (entry["abs_impact"] / total_abs) * 100, 1
                    ) if total_abs > 0 else 0.0

                shap_drivers = top_entries
            except Exception:
                shap_drivers = []

        results.append({
            "customer_id": customer_ids[i],
            "prediction": pred,
            "churn_probability": round(prob, 4),
            "risk_level": r_level,
            "financial_exposure": exposure,
            "top_drivers": shap_drivers,
            "profile": profile
        })

    avg_prob = sanitize_float(float(probs.mean())) if len(probs) > 0 else 0.0
    analytics = compute_industry_analytics(df_raw, industry)

    return to_jsonable_deep({
        "industry": industry,
        "total_customers": len(results),
        "customers_at_risk": at_risk,
        "average_churn_probability": round(avg_prob, 4),
        "total_portfolio_financial_exposure": round(total_exposure, 2),
        "risk_summary": risk_summary,
        "analytics": analytics,
        "predictions": results
    })

@app.post("/simulate")
def simulate_retention(req: RetentionSimulateRequest):
    industry = req.industry.lower()
    model = get_model(industry)
    preprocessor = get_preprocessor(industry)

    drop_cols = ["Customer ID", "CLIENTNUM", "Churn", "Attrition_Flag", "Customer Status", "Churn Category", "Churn Reason", "Lat Long", "Churn Score"]

    df_orig = pd.DataFrame([req.original_data]).drop(columns=drop_cols, errors="ignore")
    df_mod = pd.DataFrame([req.modified_data]).drop(columns=drop_cols, errors="ignore")

    p_orig = preprocessor.transform(df_orig)
    p_mod = preprocessor.transform(df_mod)

    prob_orig = sanitize_float(float(model.predict_proba(p_orig)[0][1]))
    prob_mod = sanitize_float(float(model.predict_proba(p_mod)[0][1]))

    diff_points = round((prob_orig - prob_mod) * 100, 2)
    orig_exp = calculate_financial_exposure(req.original_data, prob_orig, industry)
    mod_exp = calculate_financial_exposure(req.modified_data, prob_mod, industry)

    return {
        "industry": industry,
        "original_probability": round(prob_orig, 4),
        "original_risk": get_risk_level(prob_orig),
        "simulated_probability": round(prob_mod, 4),
        "simulated_risk": get_risk_level(prob_mod),
        "percentage_point_improvement": diff_points,
        "original_exposure": orig_exp,
        "simulated_exposure": mod_exp
    }

@app.post("/communication/generate")
def generate_comm(req: CommunicationRequest):
    return generate_communication(
        customer_id=req.customer_id,
        industry=req.industry,
        risk_level=req.risk_level,
        churn_probability=req.churn_probability,
        top_drivers=req.top_drivers,
        recommendation=req.recommendation,
        channel=req.channel,
        tone=req.tone,
        profile=req.profile
    )

@app.post("/strategy")
def get_strategy(req: StrategyRequest):
    from app.gemini_service import generate_ai_strategy
    ai_strategy = generate_ai_strategy(
        customer_id=req.customer_id,
        industry=req.industry,
        risk_level=req.risk_level,
        churn_probability=req.churn_probability,
        top_drivers=req.top_drivers,
        profile=req.profile
    )

    exposure = calculate_financial_exposure(req.profile, req.churn_probability, req.industry)

    return {
        "customer_id":        req.customer_id,
        "industry":           req.industry,
        "risk_level":         req.risk_level,
        "churn_probability":  round(req.churn_probability, 4),
        # Core fields (FIX #3 — full structured schema)
        "summary":            ai_strategy.get("summary", ""),
        "risk_explanation":   ai_strategy.get("risk_explanation", ""),
        "risk_drivers":       ai_strategy.get("risk_drivers", []),
        "protective_factors": ai_strategy.get("protective_factors", []),
        "recommendation":     ai_strategy.get("recommendation", ""),
        "recommendations":    ai_strategy.get("recommendations", []),
        "action_items":       ai_strategy.get("action_items", []),
        "financial_exposure": exposure
    }

@app.post("/agent/chat")
def agent_chat(req: AgentChatRequest):
    msg = req.message.lower()
    industry = (req.industry or "telecom").lower()
    
    if industry == "banking":
        if "inactive" in msg or "months" in msg:
            strategy = "Assign proactive relationship manager and issue 5,000 bonus loyalty points upon card reactivation."
        elif "transaction" in msg or "spend" in msg:
            strategy = "Provide 3x reward point multiplier on next 10 dining and shopping credit card transactions."
        else:
            strategy = "Offer competitive APR reduction on revolving balance transfer to reduce churn motivation."
    elif industry == "ott":
        if "watch" in msg or "login" in msg:
            strategy = "Deploy automated email with top 5 personalized movie/show recommendations based on history."
        else:
            strategy = "Offer 3 months discounted Premium tier upgrade to drive engagement."
    else:
        if "charge" in msg or "price" in msg:
            strategy = "Apply 15% monthly discount combined with a 1-year contract upgrade."
        else:
            strategy = "Provide complimentary speed upgrade and free premium tech support package."

    return {
        "industry": industry,
        "query": req.message,
        "agent_response": strategy
    }
