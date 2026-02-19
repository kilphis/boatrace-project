
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import os
import sys
import pickle

# --- Paths ---
DATA_DIR = "data"
FILE_INPUT = os.path.join(DATA_DIR, "training_featured.csv")
FILE_MODEL = os.path.join(DATA_DIR, "model.pkl")

# --- Model Features ---
FEATURES = [
    'boat_no',
    'class_val',    # Encoded A1..B2
    'motor_p',      # Motor 2-ren
    'st_ave',       # Start Timing Avg
    'st_diff',      # Diff from race mean
    'motor_rank',   # Rank in race
    'fl',           # Flying count
]
TARGET = 'flag_2rentai' # 1 if <= 2nd place, else 0

def load_data(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        sys.exit(1)
    return pd.read_csv(filepath)

def train_phase4():
    print("Starting Phase 4: Training & Evaluation...")
    
    # 1. Load Data
    print("  Loading Dataset...")
    df = load_data(FILE_INPUT)
    print(f"    Total Rows: {len(df)}")
    
    # Check if target exists
    if TARGET not in df.columns:
        print(f"Error: Target column '{TARGET}' not found.")
        return

    # Check for NaN in features
    # Fill NaN with 0 or drop? LightGBM handles NaN, but simple fill is safer for now.
    X = df[FEATURES].fillna(0)
    y = df[TARGET]

    # 2. Split Data (Train / Test)
    # Ideally split by DATE or RACE_ID to avoid leakage (e.g. same race in both train/test)
    # But for simplicity with small data, random split.
    # TODO: Implement TimeSeriesSplit in PROJECT5 v2
    
    print("  Splitting Data (80% Train, 20% Test)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"    Train size: {len(X_train)}")
    print(f"    Test size: {len(X_test)}")

    # 3. Train Model (LightGBM)
    print("  Training LightGBM Model...")
    
    # Create Dataset for LightGBM
    lgb_train = lgb.Dataset(X_train, y_train)
    lgb_eval = lgb.Dataset(X_test, y_test, reference=lgb_train)
    
    params = {
        'objective': 'binary',
        'metric': 'auc', # Area Under Curve
        'verbosity': -1,
        'boosting_type': 'gbdt',
        'seed': 42
    }
    
    # Train
    model = lgb.train(
        params,
        lgb_train,
        valid_sets=[lgb_train, lgb_eval],
        callbacks=[lgb.log_evaluation(10)] # Log every 10 iter
    )
    
    # 4. Evaluation
    print("  Evaluating Model...")
    y_pred_prob = model.predict(X_test, num_iteration=model.best_iteration)
    y_pred = [1 if p >= 0.5 else 0 for p in y_pred_prob]
    
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred_prob)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    
    print(f"\n  [Result]")
    print(f"    Accuracy : {acc:.4f}")
    print(f"    AUC      : {auc:.4f}")
    print(f"    Precision: {prec:.4f}")
    print(f"    Recall   : {rec:.4f}")
    
    # Feature Importance
    importance = model.feature_importance(importance_type='gain')
    feature_name = model.feature_name()
    print("\n  [Feature Importance (Gain)]")
    for name, imp in sorted(zip(feature_name, importance), key=lambda x: x[1], reverse=True):
        print(f"    {name}: {imp:.4f}")

    # 5. Save Model
    print(f"\n  Saving Model to {FILE_MODEL}...")
    with open(FILE_MODEL, 'wb') as f:
        pickle.dump(model, f)
        
    print("Phase 4 Completed Successfully.")

if __name__ == "__main__":
    train_phase4()
