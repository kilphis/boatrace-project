
import pandas as pd
import os
import sys

# Define Paths
DATA_DIR = "data"
FILE_INPUT = os.path.join(DATA_DIR, "training_base.csv")
FILE_OUTPUT = os.path.join(DATA_DIR, "training_featured.csv")

def load_data(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File not found {filepath}")
        sys.exit(1)
    return pd.read_csv(filepath)

def encode_class(cls_str):
    """
    Encode racer class: A1->4, A2->3, B1->2, B2->1, others->1
    """
    mapping = {'A1': 4, 'A2': 3, 'B1': 2, 'B2': 1}
    return mapping.get(cls_str, 1)

def feature_engineering_phase3():
    print("Starting Phase 3: Feature Engineering...")
    
    # 1. Load Data
    print(f"  Loading {FILE_INPUT}...")
    df = load_data(FILE_INPUT)
    print(f"    Rows: {len(df)}")
    
    # 2. Preprocessing / Type Conversion
    # Ensure numeric types
    numeric_cols = ['motor_p', 'st_ave', 'fl', 'boat_no']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 3. Feature Generation
    print("  Generating Features...")

    # [Feature] Class Encoding
    # Convert 'A1' etc to 4,3,2,1
    df['class_val'] = df['class'].apply(encode_class)
    
    # [Feature] Relative Metrics (Group by Race)
    # Calculate Race Averages
    print("    Calculating relative metrics (ST difference, Motor rank)...")
    
    # Group by race_id
    grouped = df.groupby('race_id')
    
    # Average ST in the race
    df['race_mean_st'] = grouped['st_ave'].transform('mean')
    # Deviation from race average (Higher is worse for ST, but let's just make it simple diff)
    # Usually ST 0.10 is better than 0.20. 
    # diff = my_st - mean_st. Negative is faster than average.
    df['st_diff'] = df['st_ave'] - df['race_mean_st']
    
    # Motor Rank in the race (1 to 6) based on motor_p
    df['motor_rank'] = grouped['motor_p'].rank(ascending=False, method='min')
    
    # [Feature] Boat One-Hot? 
    # Boat number is ordinal/categorical but highly correlated with result.
    # LightGBM can handle it as int or category. We keep 'boat_no'.
    
    # [Feature] Stadium ID
    # Keep as is (int).
    
    # 4. Select Columns for Training
    # We keep identifiers for reference, but define feature list.
    # We will save everything, but maybe mark features in a separate list or just usage convention.
    # For this file, we just save the augmented dataframe.
    
    print("  Columns added: class_val, st_diff, motor_rank")
    
    # 5. Save
    print(f"  Saving to {FILE_OUTPUT}...")
    df.to_csv(FILE_OUTPUT, index=False, encoding='utf-8-sig')
    print("Phase 3 Completed Successfully.")

if __name__ == "__main__":
    feature_engineering_phase3()
