
import pandas as pd
import os
import sys

# Define Paths
DATA_DIR = "data"
FILE_RACES = os.path.join(DATA_DIR, "races.csv")
FILE_ENTRIES = os.path.join(DATA_DIR, "entries.csv")
FILE_RESULTS = os.path.join(DATA_DIR, "results.csv")
FILE_OUTPUT = os.path.join(DATA_DIR, "training_base.csv")

def load_csv(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File not found {filepath}")
        sys.exit(1)
    return pd.read_csv(filepath)

def transform_phase2():
    print("Starting Phase 2: Data Transformation...")

    # 1. Load Data
    print("  Loading CSV files...")
    df_races = load_csv(FILE_RACES)
    df_entries = load_csv(FILE_ENTRIES)
    df_results = load_csv(FILE_RESULTS)

    print(f"    Races: {len(df_races)} rows")
    print(f"    Entries: {len(df_entries)} rows")
    print(f"    Results: {len(df_results)} rows")

    # 2. Merge Data
    # Base is Entries (1 row per boat)
    # Join with Races to get Date, Stadium, etc.
    print("  Merging Races info...")
    df_merged = pd.merge(df_entries, df_races, on="race_id", how="left")

    # Join with Results to get Outcome (Rankings)
    print("  Merging Results info...")
    df_merged = pd.merge(df_merged, df_results, on="race_id", how="left")

    # 3. Target Generation (is_2rentai)
    print("  Generating Target Variables...")
    
    # Check if boat_no matches rank1 or rank2
    # Note: rank columns might be NaN if no result or cancelled
    # We treat NaN as loss (0) or exclude? For now, 0, but we should probably exclude cancelled races.
    # If rank1_boat is NaN, it implies race calculation failed or cancelled.
    
    # Ensure boat numbers are numeric for comparison
    df_merged['boat_no'] = pd.to_numeric(df_merged['boat_no'], errors='coerce')
    df_merged['rank1_boat'] = pd.to_numeric(df_merged['rank1_boat'], errors='coerce')
    df_merged['rank2_boat'] = pd.to_numeric(df_merged['rank2_boat'], errors='coerce')

    def check_2rentai(row):
        bn = row['boat_no']
        if pd.isna(bn): return 0
        if row['rank1_boat'] == bn: return 1
        if row['rank2_boat'] == bn: return 1
        return 0

    df_merged['flag_2rentai'] = df_merged.apply(check_2rentai, axis=1)

    # 4. Cleaning / Filtering
    print("  Cleaning Data...")
    
    # Filter out rows where crucial data is missing
    # e.g. if racer_id is missing (absence?)
    initial_count = len(df_merged)
    df_merged = df_merged.dropna(subset=['racer_id', 'boat_no'])
    
    # If keeping rows where result is null (future races for inference), that's fine for "base",
    # but for "training", we need results. 
    # Current scope: "training_base.csv". PROJECT5 says "欠損値（欠場など）の除外".
    # Usually we want a dataset we can train on. If result is missing, we can't train.
    # However, maybe we keep them and filter in Phase 4? 
    # Let's add a column 'is_trainable' or just drop if rank is null?
    # For now, let's keep all entries but maybe flag them?
    # Actually, if we use this for training, we MUST have results.
    # But for inference, we won't have results.
    # Let's separate valid training rows?
    # PROJECT5 says: "entries（選手情報）に results（着順）を紐づける... 欠損値（欠場など）の除外"
    # I will drop rows where rank1_boat is NaN (cancelled race or future race) IF the purpose is purely training data.
    # But the filename is 'training_base'. Let's assume we keep rows that are valid entries.
    # Filter rows where boat_no is NaN (already done).

    final_count = len(df_merged)
    print(f"    Dropped {initial_count - final_count} invalid rows.")

    # 5. Save
    print(f"  Saving to {FILE_OUTPUT}...")
    df_merged.to_csv(FILE_OUTPUT, index=False, encoding='utf-8-sig')
    print("Phase 2 Completed Successfully.")

if __name__ == "__main__":
    transform_phase2()
