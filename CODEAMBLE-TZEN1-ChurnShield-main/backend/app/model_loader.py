import joblib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRIMARY_ML_DIR = os.path.join(BASE_DIR, "saved_models")
ALT_ML_DIR = os.path.join(BASE_DIR, "ml", "saved_model")

_models = {}
_preprocessors = {}

def _resolve_path(filename: str) -> str:
    p1 = os.path.join(PRIMARY_ML_DIR, filename)
    if os.path.exists(p1):
        return p1
    p2 = os.path.join(ALT_ML_DIR, filename)
    if os.path.exists(p2):
        return p2
    return p1

def get_model(domain: str = "telecom"):
    domain = domain.lower()
    if domain not in _models:
        model_path = _resolve_path(f"xgboost_{domain}.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"XGBoost model for domain '{domain}' not found at {model_path}")
        _models[domain] = joblib.load(model_path)
    return _models[domain]

def get_preprocessor(domain: str = "telecom"):
    domain = domain.lower()
    if domain not in _preprocessors:
        prep_path = _resolve_path(f"preprocessor_{domain}.pkl")
        if not os.path.exists(prep_path):
            raise FileNotFoundError(f"Preprocessor for domain '{domain}' not found at {prep_path}")
        _preprocessors[domain] = joblib.load(prep_path)
    return _preprocessors[domain]
