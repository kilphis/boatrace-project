import sys
import os
import pandas as pd
from datetime import date, timedelta
import time
from typing import Dict, Any, List
import requests
from selenium.common.exceptions import WebDriverException

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

# --- Resume Capability ---
def get_existing_race_ids():
    if not os.path.exists(FILE_RACES):
        return set()
    try:
        df = pd.read_csv(FILE_RACES, usecols=['race_id'])
        return set(df['race_id'].unique())
    except Exception:
        return set()

def collect_data_phase1(start_date: date, end_date: date, limit_races: int = 12):
    ensure_data_dir()
    boatrace = PyJPBoatrace()
    
    existing_races = get_existing_race_ids()
    print(f"Found {len(existing_races)} existing races. Skipping these...")
    
    print(f"Starting data collection Phase 1: {start_date} to {end_date}")
    
    current_date = start_date
    while current_date <= end_date:
        print(f"\nTarget Date: {current_date}")
        
        # Retry mechanism for stadium fetching
        stadiums = {}
        for attempt in range(3):
            try:
                stadiums = boatrace.get_stadiums(current_date)
                break
            except (requests.exceptions.RequestException, WebDriverException) as e:
                print(f"  Network/Browser Error fetching stadiums (Attempt {attempt+1}/3): {e}")
                time.sleep(5)
            except Exception as e:
                print(f"  Fatal Error fetching stadiums (Parse error?): {e}")
                break # Exit retry loop on structural error
        
        if not stadiums:
            print(f"  Failed to fetch stadiums for {current_date}. Skipping date.")
            current_date += timedelta(days=1)
            continue
            
        active_stadiums = []
        for name, data in stadiums.items():
            if name in ['date', 'status']: continue
            
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
            # Let's check race 1 to limit_races.
            missing_any = False
            for r in range(1, limit_races + 1):
                 rid_check = get_race_id(current_date, sid, r)
                 if rid_check not in existing_races:
                     missing_any = True
                     break
            
            if not missing_any:
                print(f"    [{sname}] All races exist. Skipping.")
                continue

            print(f"    [{sname} (ID:{sid})]")
            
            # 2. Get 12 Races Overview
            races_overview = {}
            for attempt in range(3):
                try:
                    races_overview = boatrace.get_12races(current_date, sid)
                    time.sleep(1)
                    break
                except (requests.exceptions.RequestException, WebDriverException) as e:
                    print(f"      Network Error fetching 12races (Attempt {attempt+1}/3): {e}")
                    time.sleep(5)
                except Exception as e:
                    print(f"      Fatal Error fetching 12races: {e}")
                    break

            races_buffer = []
            entries_buffer = []
            results_buffer = []

            for race_no in range(1, limit_races + 1):
                race_id = get_race_id(current_date, sid, race_no)
                
                # SKIP if already exists
                if race_id in existing_races:
                    continue
                
                race_key = f"{race_no}R"
                overview = races_overview.get(race_key, {})
                deadline = overview.get('vote_limit', '')
                
                # 3. Get Race Info (Entries)
                info = {}
                for attempt in range(3):
                    try:
                        info = boatrace.get_race_info(current_date, sid, race_no)
                        time.sleep(1)
                        break
                    except (requests.exceptions.RequestException, WebDriverException) as e:
                        print(f"      R{race_no:02d} Network Error (Attempt {attempt+1}): {e}")
                        time.sleep(3)
                    except Exception as e:
                        print(f"      R{race_no:02d} Fatal Info Error: {e}")
                        break
                
                if not info:
                    print(f"      R{race_no:02d}: Failed to get info. Skipping race.")
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
                        "motor_p": b_data.get("motor_in2nd"),
                        "st_ave": b_data.get("aveST"),
                        "fl": b_data.get("F"),
                    })
                
                # 4. Get Race Result
                res = {}
                for attempt in range(3):
                    try:
                        res = boatrace.get_race_result(current_date, sid, race_no)
                        time.sleep(1)
                        break
                    except (requests.exceptions.RequestException, WebDriverException) as e:
                        print(f"      R{race_no:02d} Network Error (Attempt {attempt+1}): {e}")
                        time.sleep(3)
                    except Exception as e:
                        # Sometimes result doesn't exist (cancelled), not always error.
                        # But pyjpboatrace might raise error if page structure is diff due to cancellation.
                        print(f"      R{race_no:02d} Result Parsing Error (or Cancelled): {e}")
                        break # Do not retry on parse error

                if res and 'result' in res:
                    rank_data = res.get('result', [])
                    payoff_data = res.get('payoff', {}).get('trifecta', {})
                    payoff_3t = payoff_data.get('payoff')
                    if isinstance(payoff_3t, list): payoff_3t = payoff_3t[0]
                    kimarite = res.get('kimarite', '')
                    
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
            if races_buffer:
                append_to_csv(FILE_RACES, races_buffer, COLS_RACES)
                append_to_csv(FILE_ENTRIES, entries_buffer, COLS_ENTRIES)
                append_to_csv(FILE_RESULTS, results_buffer, COLS_RESULTS)
                
                # Update known existing races in memory to avoid re-checking in same run if logic changes
                for r in races_buffer:
                    existing_races.add(r['race_id'])
        
        current_date += timedelta(days=1)

if __name__ == "__main__":
    # Collect data for the last 2 years by default
    # Or simple fixed range for now as per PROJECT5.md roadmap (e.g. 1-2 years)
    
    # 2024-01-01 to Yesterday
    start_date = date(2024, 1, 1)
    end_date = date.today() - timedelta(days=1)
    
    # Check if user provided args (simple check)
    if len(sys.argv) >= 3:
        try:
            start_date = date.fromisoformat(sys.argv[1])
            end_date = date.fromisoformat(sys.argv[2])
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
            
    print(f"!!! Starting Robust Data Collection: {start_date} -> {end_date} !!!")
    print("Resume capability enabled. Existing races will be skipped.")
    print("Press Ctrl+C to stop safely.")
    time.sleep(3)
    
    collect_data_phase1(start_date, end_date, limit_races=12)
