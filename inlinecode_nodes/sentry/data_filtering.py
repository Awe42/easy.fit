import json
from datetime import datetime

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
    - Screen time and productivity (excessive use may indicate stress/isolation)
    - Location patterns (isolation indicators)
    - Calendar events (upcoming stressors)
    
    Output JSON keys:
    - timestamp: ISO timestamp of the data collection
    - user_age: User's age (demographic context)
    - occupation: User's occupation (demographic context)
    - stress_data: Direct stress measurements including avg/max stress levels, duration, and analysis
    - heart_rate: Heart rate summary (max, min, avg, resting), recent samples, HR range, and elevation above resting
    - health_scores: Recovery, activity, and sleep scores from wearable device
    - blood_pressure: Systolic and diastolic blood pressure with timestamp
    - hydration: Hydration level percentage, daily water intake, and status (e.g., DEHYDRATED)
    - menstruation_status: Current cycle phase, day in cycle, and symptoms (if applicable)
    - historical_trends: 7-day averages for stress, heart rate, and sleep score, plus daily data array
    - upcoming_health_appointments: List of upcoming health-related calendar events (if applicable)
    - productivity_analysis: Screen time productivity metrics including pulse score, total hours, category breakdown, top activities, and unproductive time
    - upcoming_events: List of upcoming calendar events with summary, status, description, start time, and location
    - location_patterns: Number of places visited, time spent at home, and current location
    """
    
    stress_indicators = {}
    
    # Get timestamp for context
    if "terra" in data and "meta" in data["terra"]:
        stress_indicators["timestamp"] = data["terra"]["meta"].get("timestamp")
    
    # User context
    if "user_profile" in data:
        stress_indicators["user_age"] = data["user_profile"].get("age")
        stress_indicators["occupation"] = data["user_profile"].get("occupation")
    
    # Health data from Terra API
    if "terra" in data:
        terra_data = data["terra"]
        
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
    
    # RescueTime - screen time and productivity (stress indicator)
    if "rescuetime" in data:
        rescue_data = data["rescuetime"]
        stress_indicators["productivity_analysis"] = {
            "productivity_pulse": rescue_data.get("productivity_pulse"),
            "total_hours": rescue_data.get("total_hours"),
            "category_breakdown": rescue_data.get("category_breakdown", []),
            "top_activities": rescue_data.get("top_activities", [])
        }
        
        # Flag excessive unproductive time
        category_breakdown = rescue_data.get("category_breakdown", [])
        unproductive_time = sum(
            cat.get("time_spent_seconds", 0) 
            for cat in category_breakdown 
            if cat.get("productivity_score", 0) < 0
        )
        stress_indicators["productivity_analysis"]["unproductive_time_hours"] = unproductive_time / 3600
    
    # Google Calendar - upcoming events (potential stressors)
    if "gcal" in data and "items" in data["gcal"]:
        events = data["gcal"]["items"]
        stress_indicators["upcoming_events"] = []
        
        for event in events:
            event_info = {
                "summary": event.get("summary"),
                "status": event.get("status"),
                "description": event.get("description"),
                "start": event.get("start", {}).get("dateTime"),
                "location": event.get("location")
            }
            stress_indicators["upcoming_events"].append(event_info)
    
    # Google Maps - location patterns (isolation indicator)
    if "gmaps" in data and "timelineObjects" in data["gmaps"]:
        timeline = data["gmaps"]["timelineObjects"]
        
        # Calculate time at home
        home_time_hours = 0
        total_places = 0
        current_location = None
        
        for obj in timeline:
            if "placeVisit" in obj:
                place = obj["placeVisit"]
                location = place.get("location", {})
                duration = place.get("duration", {})
                
                if place.get("isCurrentLocation"):
                    current_location = location.get("name")
                
                # Calculate duration
                if "startTimestamp" in duration and "endTimestamp" in duration:
                    start = datetime.fromisoformat(duration["startTimestamp"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(duration["endTimestamp"].replace("Z", "+00:00"))
                    hours = (end - start).total_seconds() / 3600
                    
                    if location.get("name") == "Home":
                        home_time_hours += hours
                
                total_places += 1
        
        stress_indicators["location_patterns"] = {
            "total_places_visited": total_places,
            "home_time_hours": round(home_time_hours, 2),
            "current_location": current_location
        }
    
    return stress_indicators

############ TESTING ############
# Load test data:
# with open("../../mock_data/sentry_input_test_01_retired_person.json", "r") as f:
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


