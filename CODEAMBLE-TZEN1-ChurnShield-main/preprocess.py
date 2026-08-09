import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
import joblib
import os

# ── TELECOM SPECIFIC DROP LIST (Section 8) ───────────────────────────
TELECOM_DROP_COLUMNS = [
    "Churn",
    "Churn Category",
    "Churn Reason",
    "Churn Score",
    "Customer Status",
    "Customer ID",
    "Country",
    "City",
    "State",
    "Zip Code",
    "Lat Long",
    "Latitude",
    "Longitude",
    "Population",
    "Quarter",
    "Total Revenue",
    "CLIENTNUM",
    "Attrition_Flag",
    "Unnamed: 5"
]

GENERIC_DROP_COLS = ["Customer ID", "CLIENTNUM", "Attrition_Flag", "Customer Status", "Churn Category", "Churn Reason", "Lat Long"]
TARGET_COL = "Churn"

DATASETS = {
    "telecom": ["train.csv", "telecom_churn_dataset.csv"],
    "ott": ["ott_churn_dataset.csv"],
    "banking": ["BankChurners.csv"]
}

SAVE_PATHS = ["saved_models", os.path.join("ml", "saved_model")]
PROCESSED_DATA_PATH = "processed_data"

for sp in SAVE_PATHS:
    os.makedirs(sp, exist_ok=True)
os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)

def run_preprocessing():
    print("=" * 80)
    print(" CHURNSHIELD TELECOM & MULTI-INDUSTRY DATASET PREPROCESSING PIPELINE")
    print("=" * 80)

    # ── 1. TELECOM PREPROCESSING PIPELINE ─────────────────────────────────
    telecom_file = None
    for tf in ["train.csv", "telecom_churn_dataset.csv"]:
        if os.path.exists(tf):
            telecom_file = tf
            break

    if telecom_file:
        print(f"\n--- [TELECOM] Loading authoritative dataset: {telecom_file} ---")
        df_telecom = pd.read_csv(telecom_file)
        df_telecom = df_telecom.loc[:, ~df_telecom.columns.str.contains('^Unnamed')]

        print(f"Original Telecom dataset shape: {df_telecom.shape}")
        print(f"Original columns count: {len(df_telecom.columns)}")
        print(f"Target distribution ('Churn'): {df_telecom['Churn'].value_counts().to_dict()}")

        # Separate ground-truth target
        y_telecom = df_telecom[TARGET_COL]

        # Identify existing columns to drop for Telecom feature matrix
        dropped_cols = [c for c in TELECOM_DROP_COLUMNS if c in df_telecom.columns]
        X_telecom = df_telecom.drop(columns=dropped_cols, errors="ignore")

        print(f"Dropped non-feature columns ({len(dropped_cols)}): {dropped_cols}")
        print(f"Final Telecom feature columns count: {len(X_telecom.columns)}")
        print(f"Final Telecom input features: {list(X_telecom.columns)}")

        # 80/20 Stratified Train/Test Split BEFORE fitting preprocessor
        X_train_telecom, X_test_telecom, y_train_telecom, y_test_telecom = train_test_split(
            X_telecom, y_telecom, test_size=0.20, random_state=42, stratify=y_telecom
        )

        print(f"Training shape: {X_train_telecom.shape}, Testing shape: {X_test_telecom.shape}")

        num_cols_t = X_train_telecom.select_dtypes(include=["int64", "float64"]).columns.tolist()
        cat_cols_t = X_train_telecom.select_dtypes(include=["object", "category"]).columns.tolist()

        print(f"Numerical feature count: {len(num_cols_t)} -> {num_cols_t}")
        print(f"Categorical feature count: {len(cat_cols_t)} -> {cat_cols_t}")

        num_transformer = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="median"))
        ])

        cat_transformer = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])

        preprocessor_telecom = ColumnTransformer(
            transformers=[
                ("num", num_transformer, num_cols_t),
                ("cat", cat_transformer, cat_cols_t)
            ]
        )

        # Fit preprocessor ONLY on X_train_telecom to avoid data leakage
        preprocessor_telecom.fit(X_train_telecom)

        # Save preprocessor_telecom.pkl to saved_models and ml/saved_model
        for sp in SAVE_PATHS:
            joblib.dump(preprocessor_telecom, os.path.join(sp, "preprocessor_telecom.pkl"))

        X_train_t_trans = preprocessor_telecom.transform(X_train_telecom)
        X_test_t_trans = preprocessor_telecom.transform(X_test_telecom)

        cat_encoder_t = preprocessor_telecom.named_transformers_["cat"].named_steps["encoder"]
        cat_feat_names_t = cat_encoder_t.get_feature_names_out(cat_cols_t).tolist() if cat_cols_t else []
        feat_names_t = num_cols_t + cat_feat_names_t

        train_proc_telecom = pd.DataFrame(X_train_t_trans, columns=feat_names_t)
        train_proc_telecom[TARGET_COL] = y_train_telecom.values

        test_proc_telecom = pd.DataFrame(X_test_t_trans, columns=feat_names_t)
        test_proc_telecom[TARGET_COL] = y_test_telecom.values

        train_proc_telecom.to_csv(os.path.join(PROCESSED_DATA_PATH, "train_telecom.csv"), index=False)
        test_proc_telecom.to_csv(os.path.join(PROCESSED_DATA_PATH, "test_telecom.csv"), index=False)

        print("[TELECOM] Preprocessing complete.")
        print(f"  Saved preprocessor_telecom.pkl to {SAVE_PATHS}")
        print(f"  Saved processed train/test datasets to {PROCESSED_DATA_PATH}/")

    # ── 2. OTT & BANKING PIPELINES (UNCHANGED ARCHITECTURE) ─────────────────────
    for domain in ["ott", "banking"]:
        file_candidates = DATASETS[domain]
        filename = None
        for fc in file_candidates:
            if os.path.exists(fc):
                filename = fc
                break

        if not filename:
            print(f"Skipping {domain}: file not found.")
            continue

        print(f"\n--- [{domain.upper()}] Processing from: {filename} ---")
        df_other = pd.read_csv(filename)
        df_other = df_other.loc[:, ~df_other.columns.str.contains('^Unnamed')]

        if domain == "banking" and "Attrition_Flag" in df_other.columns:
            df_other[TARGET_COL] = df_other["Attrition_Flag"].apply(lambda x: 1 if str(x).strip() == "Attrited Customer" else 0)

        dropped_cols_other = [c for c in GENERIC_DROP_COLS + [TARGET_COL] if c in df_other.columns]
        X_other = df_other.drop(columns=dropped_cols_other, errors="ignore")
        y_other = df_other[TARGET_COL]

        X_tr, X_te, y_tr, y_te = train_test_split(
            X_other, y_other, test_size=0.20, random_state=42, stratify=y_other
        )

        num_cols = X_tr.select_dtypes(include=["int64", "float64"]).columns.tolist()
        cat_cols = X_tr.select_dtypes(include=["object", "category"]).columns.tolist()

        num_tf = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])
        cat_tf = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])

        prep = ColumnTransformer(transformers=[
            ("num", num_tf, num_cols),
            ("cat", cat_tf, cat_cols)
        ])

        prep.fit(X_tr)

        for sp in SAVE_PATHS:
            joblib.dump(prep, os.path.join(sp, f"preprocessor_{domain}.pkl"))

        X_tr_trans = prep.transform(X_tr)
        X_te_trans = prep.transform(X_te)

        cat_enc = prep.named_transformers_["cat"].named_steps["encoder"]
        cat_fn = cat_enc.get_feature_names_out(cat_cols).tolist() if cat_cols else []
        fn = num_cols + cat_fn

        tr_df = pd.DataFrame(X_tr_trans, columns=fn)
        tr_df[TARGET_COL] = y_tr.values

        te_df = pd.DataFrame(X_te_trans, columns=fn)
        te_df[TARGET_COL] = y_te.values

        tr_df.to_csv(os.path.join(PROCESSED_DATA_PATH, f"train_{domain}.csv"), index=False)
        te_df.to_csv(os.path.join(PROCESSED_DATA_PATH, f"test_{domain}.csv"), index=False)

        print(f"[{domain.upper()}] Preprocessing complete.")
        print(f"  Saved preprocessor_{domain}.pkl to {SAVE_PATHS}")

if __name__ == "__main__":
    run_preprocessing()
