
import sys
import os
import pandas as pd
from datetime import date, timedelta
import time
from typing import Dict, Any, List

# Add the local pyjpboatrace directory to path
sys.path.append(os.path.abspath("pyjpboatrace"))
from pyjpboatrace import PyJPBoatrace
from pyjpboatrace.const import STADIUMS_MAP

# Reverse map: Name -> ID
NAME_TO_ID = {name: sid for sid, name in STADIUMS_MAP}

# --- Data File Definitions ---
DATA_DIR = "data"
FILE_RACES = os.path.join(DATA_DIR, "races.csv")
FILE_ENTRIES = os.path.join(DATA_DIR, "entries.csv")
FILE_RESULTS = os.path.join(DATA_DIR, "results.csv")

# --- Column definitions (Must match CSV headers) ---
COLS_RACES = ["race_id", "date", "stadium_id", "race_no", "title", "deadline"]
COLS_ENTRIES = ["race_id", "boat_no", "racer_id", "name", "class", "motor_p", "st_ave", "fl"]
COLS_RESULTS = ["race_id", "rank1_boat", "rank2_boat", "rank3_boat", "payoff_3t", "win_method"]

def get_race_id(d: date, stadium_id: int, race_no: int) -> str:
    """Generate unique race_id: YYYYMMDD_SS_RR"""
    return f"{d.strftime('%Y%m%d')}_{stadium_id:02d}_{race_no:02d}"

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def append_to_csv(filepath: str, data: List[Dict], columns: List[str]):
    """Append list of dicts to CSV. Create header if file doesn't exist."""
    if not data:
        return
        
    # Create DataFrame with explicit columns to ensure order and avoid extras
    df = pd.DataFrame(data, columns=columns)
    
    # Check if we need to write header (if file doesn't exist)
    file_exists = os.path.exists(filepath)
    
    # Write to CSV
    df.to_csv(filepath, mode='a', index=False, header=not file_exists, encoding='utf-8-sig')

def collect_data_phase1(start_date: date, end_date: date, limit_races: int = 12):
    ensure_data_dir()
    boatrace = PyJPBoatrace()
    
    print(f"Starting data collection Phase 1: {start_date} to {end_date}")
    
    current_date = start_date
    while current_date <= end_date:
        print(f"\nTarget Date: {current_date}")
        
        # 1. Get Stadiums
        try:
            stadiums = boatrace.get_stadiums(current_date)
        except Exception as e:
            print(f"  Error fetching stadiums: {e}")
            current_date += timedelta(days=1)
            continue
            
        active_stadiums = []
        for name, data in stadiums.items():
            if name in ['date', 'status']: continue
            
            # Find ID
            sid = NAME_TO_ID.get(name)
            if not sid:
                for k, v in NAME_TO_ID.items():
                    if k in name:
                        sid = v
                        break
            if sid:
                active_stadiums.append((sid, name))
        
        print(f"  Active Stadiums: {len(active_stadiums)} venues")
        
        for sid, sname in active_stadiums:
            print(f"    [{sname} (ID:{sid})]")
            
            # 2. Get 12 Races Overview (for Deadline, Status)
            try:
                races_overview = boatrace.get_12races(current_date, sid)
                time.sleep(1) # Sleep after request
            except Exception as e:
                print(f"      Error fetching 12races: {e}")
                continue

            races_buffer = []
            entries_buffer = []
            results_buffer = []

            for race_no in range(1, limit_races + 1):
                race_id = get_race_id(current_date, sid, race_no)
                race_key = f"{race_no}R"
                
                overview = races_overview.get(race_key, {})
                deadline = overview.get('vote_limit', '')
                
                # 3. Get Race Info (Entries)
                try:
                    info = boatrace.get_race_info(current_date, sid, race_no)
                    time.sleep(1)
                except Exception as e:
                    print(f"      R{race_no:02d}: Info Error {e}")
                    continue
                
                # --- Build races.csv record ---
                race_title_list = info.get('race_title', [])
                title = race_title_list[0] if race_title_list else ""
                
                races_buffer.append({
                    "race_id": race_id,
                    "date": current_date,
                    "stadium_id": sid,
                    "race_no": race_no,
                    "title": title,
                    "deadline": deadline
                })
                
                # --- Build entries.csv records ---
                for b_idx in range(1, 7):
                    boat_key = f"boat{b_idx}"
                    b_data = info.get(boat_key, {})
                    
                    entries_buffer.append({
                        "race_id": race_id,
                        "boat_no": b_idx,
                        "racer_id": b_data.get("racerid"),
                        "name": b_data.get("name"),
                        "class": b_data.get("class"),
                        "motor_p": b_data.get("motor_in2nd"), # motor 2-ren-ritsu
                        "st_ave": b_data.get("aveST"),
                        "fl": b_data.get("F"), # Flying count
                    })
                
                # 4. Get Race Result
                try:
                    res = boatrace.get_race_result(current_date, sid, race_no)
                    time.sleep(1)
                except Exception as e:
                    print(f"      R{race_no:02d}: Result Error {e}")
                    continue
                
                # --- Build results.csv record ---
                # Check if race was canceled or no result
                if not res or 'result' not in res:
                    continue
                
                rank_data = res.get('result', [])
                # rank_data is usually a list of dicts: [{'rank': 1, 'boat': 1, ...}, ...]
                
                # Parse Payoff for 3-trifecta
                payoff_data = res.get('payoff', {}).get('trifecta', {})
                payoff_3t = payoff_data.get('payoff') # Might be list if multiple payouts
                if isinstance(payoff_3t, list):
                    payoff_3t = payoff_3t[0] # Take first one for simplicity or join
                
                # Parse Kimarite (Winning method)
                kimarite = res.get('kimarite', '')
                
                # Get top 3 boats
                rank1 = next((r['boat'] for r in rank_data if r['rank'] == 1), None)
                rank2 = next((r['boat'] for r in rank_data if r['rank'] == 2), None)
                rank3 = next((r['boat'] for r in rank_data if r['rank'] == 3), None)

                results_buffer.append({
                    "race_id": race_id,
                    "rank1_boat": rank1,
                    "rank2_boat": rank2,
                    "rank3_boat": rank3,
                    "payoff_3t": payoff_3t,
                    "win_method": kimarite
                })
                
                print(f"      R{race_no:02d}: OK")

            # Batch write for the stadium
            append_to_csv(FILE_RACES, races_buffer, COLS_RACES)
            append_to_csv(FILE_ENTRIES, entries_buffer, COLS_ENTRIES)
            append_to_csv(FILE_RESULTS, results_buffer, COLS_RESULTS)
        
        current_date += timedelta(days=1)

if __name__ == "__main__":
    # Example usage: Collect yesterday's data
    target_date = date.today() - timedelta(days=1)
    collect_data_phase1(target_date, target_date)
