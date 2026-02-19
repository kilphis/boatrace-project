from pyjpboatrace import PyJPBoatrace
from datetime import date, timedelta
from pprint import pprint

def test_fetch():
    boatrace = PyJPBoatrace()
    
    # Yesterday's date
    target_date = date.today() - timedelta(days=1)
    print(f"Fetching data for {target_date}...")
    
    # 1. Get stadiums
    stadiums = boatrace.get_stadiums(target_date)
    if not stadiums:
        print("No stadiums found for yesterday.")
        return
    
    # Pick the first stadium that has races
    stadium_name = ""
    for k, v in stadiums.items():
        if k != 'date':
            stadium_name = k
            break
            
    if not stadium_name:
        print("No active stadiums found.")
        return

    # Stadium IDs are usually mapped. Let's try to find the ID or use a known one.
    # Stadiums dict keys are Japanese names.
    print(f"Found stadium: {stadium_name}")
    
    # 2. Get 12 races and their results if available
    # Actually, let's use a more direct way to get results if the library supports it.
    # Looking at the README, get_stadiums returns titles.
    # We might need to iterate through stadium IDs (1 to 24).
    
    for stadium_id in range(1, 25):
        print(f"Trying Stadium ID: {stadium_id}")
        races = boatrace.get_12races(target_date, stadium_id)
        if races and '1R' in races:
            print(f"Successfully fetched races for Stadium ID: {stadium_id}")
            pprint(races['1R'])
            
            # 3. Get results for 1R
            result = boatrace.get_race_result(target_date, stadium_id, 1)
            print("\n--- Race Result Sample (1R) ---")
            pprint(result)
            break

if __name__ == "__main__":
    test_fetch()
