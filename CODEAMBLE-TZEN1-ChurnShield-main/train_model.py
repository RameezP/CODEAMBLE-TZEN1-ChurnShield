import pandas as pd
import joblib
import os
from xgboost import XGBClassifier
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
SAVE_PATHS = ["saved_models", os.path.join("ml", "saved_model")]

for sp in SAVE_PATHS:
    os.makedirs(sp, exist_ok=True)
TARGET_COL = "Churn"

def train_models():
    print("=" * 80)
    print(" CHURNSHIELD XGBOOST MODEL TRAINING & EVALUATION PIPELINE")
    print("=" * 80)

    for domain in DOMAINS:
        train_file = os.path.join(DATASET_PATH, f"train_{domain}.csv")
        test_file = os.path.join(DATASET_PATH, f"test_{domain}.csv")
        
        if not os.path.exists(train_file) or not os.path.exists(test_file):
            print(f"Skipping {domain}: dataset files not found. Run preprocess.py first.")
            continue

        train_df = pd.read_csv(train_file)
        test_df = pd.read_csv(test_file)

        X_train = train_df.drop(columns=[TARGET_COL])
        y_train = train_df[TARGET_COL]
        X_test = test_df.drop(columns=[TARGET_COL])
        y_test = test_df[TARGET_COL]

        # Calculate scale_pos_weight ONLY from training target
        n_neg = (y_train == 0).sum()
        n_pos = (y_train == 1).sum()
        scale_pos_weight = n_neg / n_pos if n_pos > 0 else 1.0

        print(f"\n--- Training {domain.upper()} XGBoost Model ---")
        print(f"Training samples: {len(X_train)} (Neg: {n_neg}, Pos: {n_pos}), scale_pos_weight: {scale_pos_weight:.4f}")
        print(f"Testing samples: {len(X_test)}")

        model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            random_state=42,
            eval_metric="logloss"
        )

        # Train ONLY on X_train and y_train
        model.fit(X_train, y_train)

        # Save model to saved_models and ml/saved_model
        for sp in SAVE_PATHS:
            model_path = os.path.join(sp, f"xgboost_{domain}.pkl")
            joblib.dump(model, model_path)
            print(f"Saved model to: {model_path}")

        # Evaluate on held-out test data
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc = roc_auc_score(y_test, y_prob)

        print("-" * 60)
        print(f" DOMAIN: {domain.upper()} TEST EVALUATION METRICS")
        print("-" * 60)
        print(f"Accuracy  : {acc:.4f}")
        print(f"Precision : {prec:.4f}")
        print(f"Recall    : {rec:.4f}")
        print(f"F1 Score  : {f1:.4f}")
        print(f"ROC-AUC   : {auc:.4f}")
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, zero_division=0))

if __name__ == "__main__":
    train_models()
