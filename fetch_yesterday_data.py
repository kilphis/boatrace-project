
import sys
import os
from datetime import date, timedelta
from pprint import pprint

# Add the local pyjpboatrace directory to path
sys.path.append(os.path.abspath("pyjpboatrace"))

from pyjpboatrace import PyJPBoatrace

def main():
    boatrace = PyJPBoatrace()
    
    # Target: Yesterday
    target_date = date.today() - timedelta(days=1)
    print(f"--- Fetching data for {target_date} ---")
    
    # 1. Get stadiums hosting races
    stadiums = boatrace.get_stadiums(target_date)
    if not stadiums:
        print("No races found for yesterday.")
        return
        
    # Filter out the 'date' key
    stadium_names = [name for name in stadiums.keys() if name != 'date']
    print(f"Stadiums active: {', '.join(stadium_names)}")
    
    # We need stadium IDs (1-24). The library usually uses IDs for other calls.
    # Let's try to get data for one stadium (e.g., ID 1: Kiryu, or iterate)
    # Most reliable way to test is to try IDs until one hits for yesterday.
    
    sample_stadium_id = None
    for sid in range(1, 25):
        races = boatrace.get_12races(target_date, sid)
        if races and '1R' in races:
            sample_stadium_id = sid
            print(f"Selected Stadium ID: {sid}")
            break
            
    if not sample_stadium_id:
        print("Could not find race data for any stadium yesterday.")
        return

    # 2. Get Result for 1R
    print(f"\n--- Result for {target_date}, Stadium {sample_stadium_id}, Race 1 ---")
    result = boatrace.get_race_result(target_date, sample_stadium_id, 1)
    pprint(result)
    
    # 3. Get Odds for 1R (Trifecta) to see what was expected
    print(f"\n--- Trifecta Odds for {target_date}, Stadium {sample_stadium_id}, Race 1 ---")
    odds = boatrace.get_odds_trifecta(target_date, sample_stadium_id, 1)
    
    # Show top 5 favorites
    sorted_odds = sorted(odds.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 9999)
    print("Top 5 Favorites (Market Expectation):")
    for combo, val in sorted_odds[:5]:
        print(f"  {combo}: {val}")

if __name__ == "__main__":
    main()
