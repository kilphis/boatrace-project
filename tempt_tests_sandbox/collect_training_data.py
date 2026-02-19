
import sys
import os
import pandas as pd
from datetime import date, timedelta
import time

# Add the local pyjpboatrace directory to path
sys.path.append(os.path.abspath("pyjpboatrace"))
from pyjpboatrace import PyJPBoatrace
from pyjpboatrace.const import STADIUMS_MAP

# Reverse map: Name -> ID
NAME_TO_ID = {name: sid for sid, name in STADIUMS_MAP}

def collect_data(days=3):
    boatrace = PyJPBoatrace()
    output_file = "boatrace_training_data.csv"
    
    # Remove existing file to start fresh for this 3-day test
    if os.path.exists(output_file):
        os.remove(output_file)
        
    write_header = True
    
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=days-1)
    
    print(f"Starting data collection from {start_date} to {end_date}...", flush=True)
    
    current_date = start_date
    while current_date <= end_date:
        print(f"\n--- Date: {current_date} ---", flush=True)
        try:
            stadiums = boatrace.get_stadiums(current_date)
            if not stadiums:
                print(f"  No data for {current_date}", flush=True)
                current_date += timedelta(days=1)
                continue
        except Exception as e:
            print(f"  Error fetching stadiums for {current_date}: {e}", flush=True)
            current_date += timedelta(days=1)
            continue
            
        active_stadium_names = [name for name in stadiums.keys() if name not in ['date', 'status']]
        print(f"Active Stadiums: {', '.join(active_stadium_names)}", flush=True)
        
        for name in active_stadium_names:
            sid = NAME_TO_ID.get(name)
            if not sid:
                # Some stadium names might have extra text like '（初日）' or similar if not matched exactly
                # Check for substring
                for k, v in NAME_TO_ID.items():
                    if k in name:
                        sid = v
                        break
                if not sid:
                    print(f"  Unknown stadium: {name}", flush=True)
                    continue
                
            print(f"  Stadium: {name} (ID:{sid})", flush=True)
            for rid in range(1, 13):
                try:
                    res = boatrace.get_race_result(current_date, sid, rid)
                    if not res or 'result' not in res:
                        continue
                        
                    weather = res.get('weather_information', {})
                    payoff = res.get('payoff', {})
                    trifecta = payoff.get('trifecta', {})
                    
                    row = {
                        'date': current_date.isoformat(),
                        'stadium_id': sid,
                        'stadium_name': name,
                        'race_id': rid,
                        'temp': weather.get('temperature'),
                        'water_temp': weather.get('water_temperature'),
                        'wind_speed': weather.get('wind_speed'),
                        'wind_dir': weather.get('wind_direction'),
                        'wave': weather.get('wave_height'),
                        'weather': weather.get('weather'),
                        'payoff_trifecta': trifecta.get('payoff'),
                        'popularity_trifecta': trifecta.get('popularity'),
                        'is_accident': 1 if len(res.get('return', [])) > 0 else 0
                    }
                    
                    # Save immediately (Append mode)
                    df_row = pd.DataFrame([row])
                    df_row.to_csv(output_file, mode='a', index=False, header=write_header, encoding='utf-8-sig')
                    write_header = False 
                    
                    print(f"    R:{rid:02d} -> Pop:{row['popularity_trifecta']} Pay:{row['payoff_trifecta']} Acc:{row['is_accident']}", flush=True)
                    
                except Exception as e:
                    print(f"    Error R:{rid}: {e}", flush=True)
                
                time.sleep(0.5)
        
        current_date += timedelta(days=1)
    
    print(f"\nDone! Data saved to {output_file}", flush=True)

if __name__ == "__main__":
    collect_data(days=3)
