import json

# Extract stress-related health data from sentry_input_data
def extract_stress_indicators(data):
    """
    Extracts all health data that can indicate stress levels.
    This includes:
    - Stress scores and analysis
    - Heart rate data (elevated HR can indicate stress)
    - Sleep scores (poor sleep correlates with stress)
    - Recovery scores
    - Blood pressure (can be elevated due to stress)
    - Hydration status (dehydration can affect stress)
    - Activity patterns (deviations from baseline)
    - Screen time (excessive use may indicate stress/isolation)
    """
    
    stress_indicators = {}
    
    # Get timestamp for context
    if "health_data_terra" in data and "meta" in data["health_data_terra"]:
        stress_indicators["timestamp"] = data["health_data_terra"]["meta"].get("timestamp")
    
    # User context
    if "user_profile" in data:
        stress_indicators["user_age"] = data["user_profile"].get("age")
        stress_indicators["occupation"] = data["user_profile"].get("occupation")
    
    # Current state snapshot - behavioral stress indicators
    if "current_state_snapshot" in data:
        snapshot = data["current_state_snapshot"]
        stress_indicators["current_state"] = {
            "timestamp": snapshot.get("timestamp"),
            "time_at_location_hours": snapshot.get("time_at_location_hours"),  # Prolonged isolation
            "steps_today": snapshot.get("steps_today"),
            "screen_time_today": snapshot.get("screen_time_today"),  # Excessive screen time
            "last_outgoing_call_days_ago": snapshot.get("last_outgoing_call_days_ago")  # Social isolation
        }
        
        # Check deviation from baseline
        if "user_profile" in data and "baselines" in data["user_profile"]:
            baseline_steps = data["user_profile"]["baselines"].get("avg_daily_steps")
            if baseline_steps:
                stress_indicators["current_state"]["steps_deviation_from_baseline"] = (
                    snapshot.get("steps_today", 0) - baseline_steps
                )
    
    # Screen time patterns (stress indicator)
    if "screen_time_history" in data:
        screen_history = data["screen_time_history"]
        current_screen = data.get("current_state_snapshot", {}).get("screen_time_today")
        avg_screen = screen_history.get("avg_daily_hours")
        
        stress_indicators["screen_time_analysis"] = {
            "avg_daily_hours": avg_screen,
            "today_hours": current_screen,
            "deviation_hours": (current_screen - avg_screen) if (current_screen and avg_screen) else None
        }
    
    # Health data from Terra API
    if "health_data_terra" in data:
        terra_data = data["health_data_terra"]
        
        # Current daily snapshot
        if "current_daily_snapshot" in terra_data:
            daily = terra_data["current_daily_snapshot"]
            
            # Stress data (direct indicator)
            if "stress_data" in daily:
                stress_indicators["stress_data"] = daily["stress_data"]
            
            # Heart rate data (elevated HR indicates stress)
            if "heart_rate_data" in daily:
                hr_data = daily["heart_rate_data"]
                stress_indicators["heart_rate"] = {
                    "summary": hr_data.get("summary"),
                    "recent_samples": hr_data.get("detailed", {}).get("hr_samples", [])
                }
                
                # Calculate HR variability indicators
                if "summary" in hr_data:
                    summary = hr_data["summary"]
                    max_hr = summary.get("max_hr_bpm")
                    min_hr = summary.get("min_hr_bpm")
                    avg_hr = summary.get("avg_hr_bpm")
                    resting_hr = summary.get("resting_hr_bpm")
                    
                    if max_hr and min_hr:
                        stress_indicators["heart_rate"]["hr_range"] = max_hr - min_hr
                    
                    if avg_hr and resting_hr:
                        stress_indicators["heart_rate"]["hr_elevation_above_resting"] = avg_hr - resting_hr
            
            # Health scores (recovery, sleep affect stress)
            if "scores" in daily:
                stress_indicators["health_scores"] = daily["scores"]
        
        # Body metrics - blood pressure and hydration
        if "body_metrics_latest" in terra_data:
            body = terra_data["body_metrics_latest"]
            
            # Blood pressure (can be elevated due to stress)
            if "measurements_data" in body:
                stress_indicators["blood_pressure"] = {
                    "systolic": body["measurements_data"].get("blood_pressure_systolic"),
                    "diastolic": body["measurements_data"].get("blood_pressure_diastolic"),
                    "timestamp": body.get("timestamp")
                }
            
            # Hydration (affects stress response)
            if "hydration_data" in body:
                stress_indicators["hydration"] = body["hydration_data"]
        
        # Menstruation status (hormonal factors affect stress)
        if "menstruation_status" in terra_data:
            mens = terra_data["menstruation_status"]
            stress_indicators["menstruation_status"] = {
                "current_phase": mens.get("current_phase_string"),
                "day_in_cycle": mens.get("day_in_cycle"),
                "symptoms": mens.get("symptoms")  # fatigue, mood_swings can indicate stress
            }
        
        # Historical data for trend analysis
        if "historical_7_days" in terra_data:
            historical = terra_data["historical_7_days"]
            stress_indicators["historical_trends"] = {
                "avg_stress_7_days": sum(day.get("avg_stress", 0) for day in historical) / len(historical) if historical else None,
                "avg_hr_7_days": sum(day.get("avg_hr", 0) for day in historical) / len(historical) if historical else None,
                "avg_sleep_score_7_days": sum(day.get("sleep_score", 0) for day in historical) / len(historical) if historical else None,
                "daily_data": historical
            }
    
    # Calendar context - upcoming health appointments may indicate stress
    if "calendar_context" in data:
        upcoming = data["calendar_context"].get("upcoming_7_days", [])
        health_appointments = [event for event in upcoming if event.get("category") == "Health"]
        if health_appointments:
            stress_indicators["upcoming_health_appointments"] = health_appointments
    
    return stress_indicators

############ TESTING ############
# Load test data:
# with open("../mock_data/sentry_input_test_01_retired_person.json", "r") as f:
#     sentry_input_data = f.read()
#################################

# Main execution
# Parse the input JSON string
data = json.loads(sentry_input_data)

# Extract stress indicators
output_data = extract_stress_indicators(data)

# Convert output to JSON string
output_json = json.dumps(output_data, indent=2)

output_json

############ TESTING ############
# print(output_json)
#################################


