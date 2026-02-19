
import pandas as pd
import numpy as np
import lightgbm as lgb
import matplotlib
matplotlib.use('Agg') # Non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import LabelEncoder
import os

def train_rough_prediction_model(csv_path="boatrace_training_data.csv"):
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    # 1. Load Data
    df = pd.read_csv(csv_path)
    if len(df) < 50:
        print(f"Warning: Only {len(df)} rows. More data is recommended for LightGBM.")
    
    # 2. Define Target (Target: 1 if Rough/Accident, 0 if Standard)
    # Rough = Payoff >= 10,000 yen (Man-shu) OR Accident happened
    df['target'] = df.apply(lambda x: 1 if x['payoff_trifecta'] >= 10000 or x['is_accident'] == 1 else 0, axis=1)
    
    print("\n--- Class Distribution ---")
    print(df['target'].value_counts())

    # 3. Feature Selection & Engineering
    # Features: Stadium, Temp, Water Temp, Wind Speed, Wave, Weather
    features = ['stadium_id', 'temp', 'water_temp', 'wind_speed', 'wind_dir', 'wave', 'weather']
    
    # Process categorical features
    le = LabelEncoder()
    df['weather'] = le.fit_transform(df['weather'].astype(str))
    
    X = df[features]
    y = df['target']

    # 4. Split Data
    # For very small data, use all for demo, but usually split
    if len(df) > 10:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    else:
        print("Dataset too small for split. Using all data for training (Demo mode).")
        X_train, y_train = X, y
        X_test, y_test = X, y

    # 5. Train LightGBM
    print("\nTraining LightGBM model...")
    params = {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'verbosity': -1,
        'boosting_type': 'gbdt',
        'random_state': 42,
        'learning_rate': 0.05,
        'num_leaves': 31,
    }
    
    train_data = lgb.Dataset(X_train, label=y_train)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
    
    model = lgb.train(
        params,
        train_data,
        valid_sets=[test_data],
        num_boost_round=100,
        callbacks=[lgb.early_stopping(stopping_rounds=10)]
    )

    # 6. Evaluation
    y_pred_prob = model.predict(X_test)
    y_pred = [1 if p >= 0.5 else 0 for p in y_pred_prob]
    
    print("\n--- Model Evaluation ---")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    
    cm = confusion_matrix(y_test, y_pred)
    if len(np.unique(y_test)) > 1:
        print("\nConfusion Matrix:")
        print(cm)
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
    else:
        print("Only one class present in test set. Classification report skipped.")

    # 7. Visualization: Confusion Matrix
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Standard', 'Rough'], yticklabels=['Standard', 'Rough'])
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix')
    plt.savefig('confusion_matrix.png')
    plt.close()
    print("Saved confusion_matrix.png")

    # 8. Feature Importance
    print("\n--- Feature Importance ---")
    importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importance()
    }).sort_values('importance', ascending=False)
    print(importance)

    # 9. Visualization: Feature Importance
    plt.figure(figsize=(8, 6))
    sns.barplot(x='importance', y='feature', data=importance)
    plt.title('Feature Importance')
    plt.tight_layout()
    plt.savefig('feature_importance.png')
    plt.close()
    print("Saved feature_importance.png")

    # 10. Save Model
    model.save_model("boatrace_rough_model.txt")
    print("\nModel saved to boatrace_rough_model.txt")

if __name__ == "__main__":
    train_rough_prediction_model()
