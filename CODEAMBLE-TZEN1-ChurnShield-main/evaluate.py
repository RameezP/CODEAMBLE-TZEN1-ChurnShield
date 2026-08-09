import pandas as pd
import joblib
import os
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

DOMAINS = ["telecom", "ott", "banking"]
DATASET_PATH = "processed_data"
SAVE_PATH = "saved_models"
TARGET_COL = "Churn"

def evaluate_models():
    print("=" * 80)
    print(" CHURNSHIELD HELD-OUT TEST EVALUATION")
    print("=" * 80)

    for domain in DOMAINS:
        test_file = os.path.join(DATASET_PATH, f"test_{domain}.csv")
        model_path = os.path.join(SAVE_PATH, f"xgboost_{domain}.pkl")
        
        if not os.path.exists(test_file) or not os.path.exists(model_path):
            print(f"Skipping {domain}: test dataset or model missing.")
            continue

        test_df = pd.read_csv(test_file)
        X_test = test_df.drop(columns=[TARGET_COL])
        y_test = test_df[TARGET_COL]

        model = joblib.load(model_path)

        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc = roc_auc_score(y_test, y_prob)

        print("-" * 60)
        print(f" STANDALONE TEST EVALUATION: {domain.upper()}")
        print("-" * 60)
        print(f"Test Samples: {len(X_test)}")
        print(f"Accuracy    : {acc:.4f}")
        print(f"Precision   : {prec:.4f}")
        print(f"Recall      : {rec:.4f}")
        print(f"F1 Score    : {f1:.4f}")
        print(f"ROC-AUC     : {auc:.4f}")
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, zero_division=0))
        print("\n")

if __name__ == "__main__":
    evaluate_models()
