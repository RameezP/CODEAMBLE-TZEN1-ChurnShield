import pandas as pd
import glob
import os
import io

import sys
sys.path.append(os.path.abspath("backend"))

from app.model_loader import get_model, get_preprocessor

csv_files = glob.glob("**/*.csv", recursive=True)

industries = ["telecom", "ott", "banking"]

print("=== CSV AUDIT REPORT FOR CHURNSHIELD ===")
for csv_path in sorted(csv_files):
    if ".system_generated" in csv_path or "brain" in csv_path:
        continue
    filename = os.path.basename(csv_path)
    print(f"\n--- Checking File: {csv_path} ---")
    try:
        df_raw = pd.read_csv(csv_path)
        print(f"Shape: {df_raw.shape}")
        cols = df_raw.columns.tolist()
        print(f"Columns ({len(cols)}): {cols[:8]}...")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        continue

    for ind in industries:
        preprocessor = get_preprocessor(ind)
        model = get_model(ind)
        num_cols = list(preprocessor.transformers_[0][2])
        cat_cols = list(preprocessor.transformers_[1][2])
        expected_cols = num_cols + cat_cols

        df_feat = df_raw.drop(columns=["Customer ID", "CLIENTNUM", "Churn", "Attrition_Flag", "Customer Status", "Churn Category", "Churn Reason", "Lat Long", "Churn Score"], errors="ignore")
        df_feat = df_feat.loc[:, ~df_feat.columns.str.contains('^Unnamed')]

        missing = [c for c in expected_cols if c not in df_feat.columns]
        matching = [c for c in expected_cols if c in df_feat.columns]
        
        status = "PASSED"
        try:
            for c in expected_cols:
                if c not in df_feat.columns:
                    df_feat[c] = float('nan')
            processed = preprocessor.transform(df_feat)
            if hasattr(processed, "toarray"):
                processed = processed.toarray()
            preds = model.predict(processed)
            probs = model.predict_proba(processed)[:, 1]
            status = f"SUCCESS (Predicted {len(preds)} rows)"
        except Exception as err:
            status = f"FAILED ({str(err)[:80]})"

        print(f"  Domain [{ind.upper()}]: Matching cols: {len(matching)}/{len(expected_cols)} -> Status: {status}")
