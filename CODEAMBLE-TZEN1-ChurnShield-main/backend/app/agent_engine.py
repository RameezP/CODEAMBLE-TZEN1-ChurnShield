import math
import pandas as pd
import numpy as np
import shap
from app.model_loader import get_model, get_preprocessor
from app.recommendation_engine import get_risk_level, calculate_financial_exposure

GEO_IGNORE = {
    "city", "zip code", "latitude", "longitude", "lat long", "lat_long",
    "cltv", "total long distance charges", "avg monthly long distance charges",
    "total charges", "total extra data charges", "total refunds"
}


def to_jsonable_deep(obj):
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64, np.float32, np.float16, float)):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return 0.0
        return round(val, 4)
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, dict):
        return {str(k): to_jsonable_deep(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, np.ndarray)):
        return [to_jsonable_deep(x) for x in obj]
    if pd.isna(obj):
        return None
    return obj



def _reverse_onehot_map(feat_name: str, profile: dict) -> tuple:
    """
    FIX #2 — Feature Name Mapping.

    Given a (possibly one-hot encoded) model feature name, returns:
        (original_attribute_name, customer_raw_value)

    Examples:
        'cat__Contract_Two year'  + profile{'Contract': 'Two Year'}
            → ('Contract', 'Two Year')

        'cat__InternetService_Fiber optic' + profile{'Internet Service': 'Fiber Optic'}
            → ('Internet Service', 'Fiber Optic')

        'num__Monthly Charge' + profile{'Monthly Charge': 89.5}
            → ('Monthly Charge', 89.5)
    """
    # Strip sklearn ColumnTransformer prefixes
    clean = feat_name.replace("num__", "").replace("cat__", "").strip()

    # Step 1: Try direct exact/fuzzy match against profile keys (numeric features)
    for profile_key, profile_val in profile.items():
        pk_norm = profile_key.lower().replace(" ", "_").replace("-", "_")
        clean_norm = clean.lower().replace(" ", "_").replace("-", "_")
        if pk_norm == clean_norm or profile_key.lower() == clean.lower():
            return (profile_key, profile_val)

    # Step 2: Try one-hot reverse mapping — feature = "OrigCol_CategoryValue"
    # Build a sorted list (longest key first) to prefer specific matches
    sorted_keys = sorted(profile.keys(), key=lambda k: len(k), reverse=True)
    for profile_key in sorted_keys:
        pk_norm = profile_key.lower().replace(" ", "_").replace("-", "_")
        clean_norm = clean.lower().replace(" ", "_").replace("-", "_")
        # Check if clean feature starts with the profile key (one-hot pattern)
        if clean_norm.startswith(pk_norm + "_"):
            # The suffix after "ProfileKey_" is the category value the encoder created
            # Return the profile's actual raw value for that column
            return (profile_key, profile.get(profile_key))

    # Step 3: Partial substring fallback for tricky cases
    for profile_key, profile_val in profile.items():
        pk_lower = profile_key.lower().replace(" ", "")
        clean_lower = clean.lower().replace("_", "").replace(" ", "")
        if pk_lower in clean_lower or clean_lower in pk_lower:
            return (profile_key, profile_val)

    # Step 4: Humanise the raw feature name as last resort
    humanized = clean.replace("_", " ").strip().title()
    return (humanized, None)


class RetentionAgentOrchestrator:
    def __init__(self, industry: str):
        self.industry = industry.lower()
        self.model = get_model(self.industry)
        self.preprocessor = get_preprocessor(self.industry)
        try:
            self.explainer = shap.TreeExplainer(self.model)
        except Exception:
            self.explainer = None

    def run_pipeline(self, customer_data: dict, customer_id: str = "CUST-001") -> dict:
        df_raw = pd.DataFrame([customer_data])

        drop_cols = [
            "Customer ID", "CLIENTNUM", "Churn", "Attrition_Flag",
            "Customer Status", "Churn Category", "Churn Reason", "Lat Long",
            "Churn Score"
        ]
        df_features = df_raw.drop(columns=drop_cols, errors="ignore")

        num_cols = list(self.preprocessor.transformers_[0][2])
        cat_cols = list(self.preprocessor.transformers_[1][2])
        for col in num_cols + cat_cols:
            if col not in df_features.columns:
                df_features[col] = np.nan

        # ── Inference ──────────────────────────────────────────────
        processed = self.preprocessor.transform(df_features)
        processed_dense = processed.toarray() if hasattr(processed, "toarray") else processed

        prediction  = int(self.model.predict(processed_dense)[0])
        probability = float(self.model.predict_proba(processed_dense)[0][1])
        risk_level  = get_risk_level(probability)

        # ── SHAP ───────────────────────────────────────────────────
        top_shap_features = []
        try:
            explainer   = self.explainer or shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(processed_dense)

            if isinstance(shap_values, list):
                shap_array = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
            elif len(shap_values.shape) == 2:
                shap_array = shap_values[0]
            else:
                shap_array = shap_values[0]

            num_feat_names   = list(self.preprocessor.transformers_[0][2])
            cat_feat_cols    = list(self.preprocessor.transformers_[1][2])
            cat_encoder      = self.preprocessor.named_transformers_["cat"].named_steps["encoder"]
            cat_feature_names = cat_encoder.get_feature_names_out(cat_feat_cols).tolist() if cat_feat_cols else []
            feature_names    = num_feat_names + cat_feature_names

            # Group SHAP values by Primary Attribute Name
            attr_shap = {}
            for fname, val in zip(feature_names, shap_array):
                if any(g in fname.lower() for g in GEO_IGNORE):
                    continue
                orig_attr, feat_val = _reverse_onehot_map(fname, customer_data)
                # Ensure it maps to an actual primary customer attribute
                if feat_val is None and orig_attr not in customer_data:
                    continue
                if orig_attr not in attr_shap:
                    val_display = feat_val if feat_val is not None else customer_data.get(orig_attr, "N/A")
                    attr_shap[orig_attr] = {"shap_sum": 0.0, "feat_val": val_display}
                attr_shap[orig_attr]["shap_sum"] += float(val)

            top_list = []
            for attr, data in attr_shap.items():
                s_val = round(data["shap_sum"], 4)
                abs_s = abs(s_val)
                top_list.append({
                    "feature":       attr,
                    "raw_feature":   attr,
                    "impact":        s_val,
                    "abs_impact":    round(abs_s, 4),
                    "direction":     "churn" if s_val > 0 else "retention",
                    "feature_value": data["feat_val"]
                })

            top_list.sort(key=lambda x: x["abs_impact"], reverse=True)
            top_n = top_list[:8]
            total_abs = sum(x["abs_impact"] for x in top_n)

            for item in top_n:
                item["importance"] = round((item["abs_impact"] / total_abs) * 100, 1) if total_abs > 0 else 0.0

            top_shap_features = top_n

        except Exception as shap_err:
            print(f"[SHAP] Warning: SHAP computation failed — {shap_err}")

        # ── Financial Exposure ─────────────────────────────────────
        financial_exposure = calculate_financial_exposure(customer_data, probability, self.industry)

        # ── Gemini AI Strategy (optional — graceful degradation) ───
        ai_strategy = {}
        try:
            from app.gemini_service import generate_ai_strategy
            ai_strategy = generate_ai_strategy(
                customer_id=customer_id,
                industry=self.industry,
                risk_level=risk_level,
                churn_probability=probability,
                top_drivers=top_shap_features,
                profile=customer_data
            )
        except Exception as gemini_err:
            print(f"[Gemini] Warning: AI strategy generation failed — {gemini_err}")

        return to_jsonable_deep({
            "customer_id":        customer_id,
            "industry":           self.industry,
            "prediction":         prediction,
            "churn_probability":  round(probability, 4),
            "risk_level":         risk_level,
            "financial_exposure": financial_exposure,
            "top_churn_drivers":  top_shap_features,
            "top_drivers":        top_shap_features,
            "strategy_summary":   ai_strategy.get("summary", ""),
            "recommendation":     ai_strategy.get("recommendation", ""),
            "action_items":       ai_strategy.get("action_items", []),
            "risk_drivers":       ai_strategy.get("risk_drivers", []),
            "protective_factors": ai_strategy.get("protective_factors", []),
            "profile":            customer_data
        })
