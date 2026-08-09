import joblib

for domain in ['telecom', 'ott', 'banking']:
    prep = joblib.load(f'saved_models/preprocessor_{domain}.pkl')
    model = joblib.load(f'saved_models/xgboost_{domain}.pkl')
    num_cols = list(prep.transformers_[0][2])
    cat_cols = list(prep.transformers_[1][2])
    cat_encoder = prep.named_transformers_['cat'].named_steps['encoder']
    cat_feature_names = cat_encoder.get_feature_names_out(cat_cols).tolist() if cat_cols else []
    feature_names = num_cols + cat_feature_names
    print(f'{domain.upper()}: preprocessor={len(feature_names)} features, model expects={model.n_features_in_}')
    print(f'  Numerical ({len(num_cols)}): {num_cols}')
    print(f'  Categorical input ({len(cat_cols)}): {cat_cols}')
    print()
