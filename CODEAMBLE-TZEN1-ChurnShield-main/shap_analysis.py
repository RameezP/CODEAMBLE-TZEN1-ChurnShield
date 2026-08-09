import pandas as pd
import joblib
import shap
import matplotlib.pyplot as plt
import os

DOMAINS = ["telecom", "ott", "banking"]
DATASET_PATH = "processed_data"
SAVE_PATH = "saved_models"
OUTPUT_PATH = "shap_outputs"

os.makedirs(OUTPUT_PATH, exist_ok=True)
TARGET_COL = "Churn"

def run_shap_analysis():
    for domain in DOMAINS:
        test_file = os.path.join(DATASET_PATH, f"test_{domain}.csv")
        model_path = os.path.join(SAVE_PATH, f"xgboost_{domain}.pkl")
        
        if not os.path.exists(test_file) or not os.path.exists(model_path):
            print(f"Skipping {domain}: dataset or model missing.")
            continue

        test_df = pd.read_csv(test_file)
        X_test = test_df.drop(columns=[TARGET_COL])
        feature_names = list(X_test.columns)

        model = joblib.load(model_path)

        explainer = shap.TreeExplainer(model)
        shap_values = explainer(X_test[:300])

        plt.figure()
        shap.summary_plot(
            shap_values.values,
            X_test[:300],
            feature_names=feature_names,
            plot_type="bar",
            show=False
        )
        plt.savefig(os.path.join(OUTPUT_PATH, f"shap_bar_{domain}.png"), bbox_inches="tight")
        plt.close()

        plt.figure()
        shap.summary_plot(
            shap_values.values,
            X_test[:300],
            feature_names=feature_names,
            show=False
        )
        plt.savefig(os.path.join(OUTPUT_PATH, f"shap_summary_{domain}.png"), bbox_inches="tight")
        plt.close()

        print(f"[{domain.upper()}] SHAP analysis complete. Saved plots to {OUTPUT_PATH}/")

def explain_customer(domain: str, input_features_df: pd.DataFrame):
    model_path = os.path.join(SAVE_PATH, f"xgboost_{domain}.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model for {domain} not found.")

    model = joblib.load(model_path)
    explainer = shap.TreeExplainer(model)
    shap_vals = explainer(input_features_df)
    
    feature_impacts = {}
    for name, val in zip(input_features_df.columns, shap_vals.values[0]):
        feature_impacts[name] = float(val)
        
    sorted_impacts = sorted(feature_impacts.items(), key=lambda x: abs(x[1]), reverse=True)
    return sorted_impacts

if __name__ == "__main__":
    run_shap_analysis()
