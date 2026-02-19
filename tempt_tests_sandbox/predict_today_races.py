
import sys
import os
import pandas as pd
from datetime import date
import lightgbm as lgb
from sklearn.preprocessing import LabelEncoder

# Add the local pyjpboatrace directory to path
sys.path.append(os.path.abspath("pyjpboatrace"))
from pyjpboatrace import PyJPBoatrace
from pyjpboatrace.const import STADIUMS_MAP

# Reverse map: Name -> ID
NAME_TO_ID = {name: sid for sid, name in STADIUMS_MAP}

def get_today_predictions():
    model_path = "boatrace_rough_model.txt"
    if not os.path.exists(model_path):
        print("Error: Model file 'boatrace_rough_model.txt' not found. Please run train_model.py first.")
        return

    # 1. Load Model
    model = lgb.Booster(model_file=model_path)
    boatrace = PyJPBoatrace()
    today = date.today()
    
    print(f"--- Predicting Today's Races ({today}) ---", flush=True)

    # 2. Get Today's Stadiums
    stadiums = boatrace.get_stadiums(today)
    if not stadiums:
        print("No stadiums holding races today.")
        return
        
    active_stadium_names = [name for name in stadiums.keys() if name not in ['date', 'status']]
    print(f"Analyzing stadiums: {', '.join(active_stadium_names)}", flush=True)

    # Output Markdown File
    md_file = "today_prediction.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# 🚤 本日のボートレース波乱度予想 ({today})\n\n")
        f.write("AIモデルが予測した「荒れやすさ」を一覧表で示します。\n")
        f.write("- **★スコア**: 星が多いほど高配当やアクシデントの可能性が高いです。\n")
        f.write("- **風速**: 5m以上は荒れ要因の筆頭です。\n\n")

    # 3. Fetch Info and Predict
    for name in active_stadium_names:
        sid = NAME_TO_ID.get(name)
        if not sid:
            for k, v in NAME_TO_ID.items():
                if k in name: sid = v; break
            if not sid: continue

        print(f"\n[Stadium: {name}]", flush=True)
        
        # Buffer for markdown table
        race_rows = []
        
        # Check all races 1-12
        for rid in range(1, 13): 
            try:
                # Get BeforeInfo (Pre-race weather)
                info = boatrace.get_before_info(today, sid, rid)
                weather = info.get('weather_information', {})
                
                # Fill features
                weather_map = {'晴': 0, '曇り': 1, '雨': 2, '雪': 3, '霧': 4}
                weather_val = weather_map.get(weather.get('weather', ''), 1) 

                input_data = pd.DataFrame([{
                    'stadium_id': sid,
                    'temp': weather.get('temperature', 15),
                    'water_temp': weather.get('water_temperature', 15),
                    'wind_speed': weather.get('wind_speed', 0),
                    'wind_dir': weather.get('wind_direction', 0),
                    'wave': weather.get('wave_height', 0),
                    'weather': weather_val
                }])

                # Predict
                prob = model.predict(input_data)[0]
                
                # Format Output
                star_count = int(prob * 5) + 1
                star = "★" * star_count
                status = "**荒れ注意**" if prob > 0.5 else "堅実"
                
                # Console Output
                print(f"  {rid:2d}R | 波乱度: {star:<5} ({prob:.1%}) -> {status}", flush=True)

                # Append to Markdown Table
                race_rows.append(f"| {rid}R | {star} | {prob:.0%} | {status} | {input_data['wind_speed'][0]}m | {input_data['wave'][0]}cm |")

            except Exception:
                # Race info likely not ready
                pass

        # Write to Markdown if we have data
        if race_rows:
            with open(md_file, "a", encoding="utf-8") as f:
                f.write(f"## 🏟️ {name}\n")
                f.write("| R | 予想 | 確率 | 判定 | 風速 | 波高 |\n")
                f.write("|---|---|---|---|---|---|\n")
                for row in race_rows:
                    f.write(row + "\n")
                f.write("\n")

    print(f"\nPredictions saved to {md_file}", flush=True)

if __name__ == "__main__":
    get_today_predictions()
