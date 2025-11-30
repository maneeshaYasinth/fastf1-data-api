# app.py

import fastf1
from flask import Flask, jsonify
import pandas as pd
import datetime

# --- FastF1 Setup ---
# Caching is essential to speed up your scripts and prevent rate limiting.
fastf1.Cache.enable_cache('./cache') 

# --- Flask App Setup ---
app = Flask(__name__)

# --- API Route: Dynamic Race Results ---

@app.route('/api/v1/race_results/<int:year>/<int:round>', methods=['GET'])
def get_race_results(year, round):
    """
    Fetches F1 race results for a specified year and round number.
    Example URL: http://127.0.0.1:5001/api/v1/race_results/2025/1
    """
    SESSION_TYPE = 'R' # Fetches the main Race session results
    
    # Simple validation to prevent trying to fetch data for the distant future
    if year > datetime.date.today().year or round < 1:
        return jsonify({
            "status": "error",
            "message": "Invalid year or round number provided."
        }), 400

    try:
        # 1. Get and Load the session data using the passed arguments
        session = fastf1.get_session(year, round, SESSION_TYPE)
        # The .load() method downloads all necessary data and saves it to your cache.
        session.load(telemetry=False, weather=False) # Only load what we need (results)

        # 2. Check if results are actually available (e.g., race not yet run)
        # Note: fastf1 uses Pandas DataFrames extensively.
        if session.results.empty:
            return jsonify({
                "status": "warning",
                "message": f"{session.event['EventName']} race data is not yet available.",
                "race": session.event['EventName']
            }), 200

        # 3. Extract, select columns, and convert to JSON
        results_df = session.results
        
        # Select common result fields and convert the Pandas DataFrame to a list of dicts (JSON format)
        final_results = results_df.loc[:, [
            'Abbreviation',
            'TeamName',
            'ClassifiedPosition',
            'Points'
        ]].to_dict('records') 

        # 4. Return the JSON response
        return jsonify({
            "status": "success",
            "race_name": session.event['EventName'],
            "year": year,
            "round": round,
            "session": session.name,
            "results": final_results
        })

    except Exception as e:
        # General error handling for network failures or bad data access
        print(f"Error processing request: {e}")
        return jsonify({
            "status": "error",
            "message": f"Could not fetch F1 data for {year} Round {round}.",
            "detail": str(e)
        }), 500


# --- Run the Application ---
if __name__ == '__main__':
    # Running on port 5001 to avoid conflicts with other local services (like your MERN app)
    app.run(debug=True, port=5001)