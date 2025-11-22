import json

def categorize_physiological_and_digital(filtered_data):
    """
    Extracts and categorizes physiological state and digital hygiene from filtered stress data.
    
    Input: filtered_data - JSON object containing stress indicators from data_filtering.py
    
    Output JSON structure:
    - physiological_state:
        - stress_level: RESTING, NORMAL, ELEVATED, or CRITICAL_HIGH
        - heart_rate_context: RESTING, NORMAL, ELEVATED_ACTIVE, or ELEVATED_SEDENTARY
        - exertion_status: SEDENTARY, OPTIMAL, or OVER_EXERTION_RISK
        - sleep_debt: WELL_RESTED, MILD_DEBT, or SEVERE_DEBT
        - hydration_status: HYDRATED or DEHYDRATED
    - digital_hygiene:
        - digital_state: DISCONNECTED, FLOW_STATE, FRAGMENTED, or DOOMSCROLLING
        - productivity_pulse: PRODUCTIVE, NEUTRAL, or DISTRACTED
        - dominant_app_category: SOCIAL_MEDIA, NEWS, WORK, ENTERTAINMENT, or UTILITY
    """
    
    result = {}
    
    # ========== PHYSIOLOGICAL STATE ==========
    physiological = {}
    
    # Categorize stress_level
    stress_data = filtered_data.get("stress_data", {})
    avg_stress = stress_data.get("avg_stress_level", 0)
    
    if avg_stress < 30:
        physiological["stress_level"] = "RESTING"
    elif avg_stress < 60:
        physiological["stress_level"] = "NORMAL"
    elif avg_stress < 80:
        physiological["stress_level"] = "ELEVATED"
    else:
        physiological["stress_level"] = "CRITICAL_HIGH"
    
    # Categorize heart_rate_context
    heart_rate = filtered_data.get("heart_rate", {})
    hr_elevation = heart_rate.get("hr_elevation_above_resting", 0)
    
    if hr_elevation < 5:
        physiological["heart_rate_context"] = "RESTING"
    elif hr_elevation < 20:
        physiological["heart_rate_context"] = "NORMAL"
    elif avg_stress > 60:  # Elevated HR with high stress = sedentary stress
        physiological["heart_rate_context"] = "ELEVATED_SEDENTARY"
    else:
        physiological["heart_rate_context"] = "ELEVATED_ACTIVE"
    
    # Categorize exertion_status (based on activity and recovery scores)
    health_scores = filtered_data.get("health_scores", {})
    activity_score = health_scores.get("activity", 50)
    recovery_score = health_scores.get("recovery", 50)
    
    if activity_score < 30:
        physiological["exertion_status"] = "SEDENTARY"
    elif activity_score > 80 and recovery_score < 40:
        physiological["exertion_status"] = "OVER_EXERTION_RISK"
    else:
        physiological["exertion_status"] = "OPTIMAL"
    
    # Categorize sleep_debt
    sleep_score = health_scores.get("sleep", 50)
    
    if sleep_score >= 70:
        physiological["sleep_debt"] = "WELL_RESTED"
    elif sleep_score >= 50:
        physiological["sleep_debt"] = "MILD_DEBT"
    else:
        physiological["sleep_debt"] = "SEVERE_DEBT"
    
    # Categorize hydration_status
    hydration = filtered_data.get("hydration", {})
    hydration_status = hydration.get("status", "").upper()
    
    if hydration_status == "DEHYDRATED":
        physiological["hydration_status"] = "DEHYDRATED"
    else:
        physiological["hydration_status"] = "HYDRATED"
    
    result["physiological_state"] = physiological
    
    # ========== DIGITAL HYGIENE ==========
    digital = {}
    
    # Analyze productivity data
    productivity = filtered_data.get("productivity_analysis", {})
    pulse = productivity.get("productivity_pulse", 50)
    total_hours = productivity.get("total_hours", 0)
    unproductive_hours = productivity.get("unproductive_time_hours", 0)
    
    # Categorize digital_state
    if total_hours < 2:
        digital["digital_state"] = "DISCONNECTED"
    elif pulse >= 60 and total_hours < 10:
        digital["digital_state"] = "FLOW_STATE"
    elif unproductive_hours > 5:
        digital["digital_state"] = "DOOMSCROLLING"
    else:
        digital["digital_state"] = "FRAGMENTED"
    
    # Categorize productivity_pulse
    if pulse >= 60:
        digital["productivity_pulse"] = "PRODUCTIVE"
    elif pulse >= 40:
        digital["productivity_pulse"] = "NEUTRAL"
    else:
        digital["productivity_pulse"] = "DISTRACTED"
    
    # Determine dominant_app_category
    categories = productivity.get("category_breakdown", [])
    if categories:
        # Find category with most time
        dominant = max(categories, key=lambda x: x.get("time_spent_seconds", 0))
        category_name = dominant.get("category", "").lower()
        
        if "social" in category_name or "networking" in category_name:
            digital["dominant_app_category"] = "SOCIAL_MEDIA"
        elif "news" in category_name:
            digital["dominant_app_category"] = "NEWS"
        elif "work" in category_name or "development" in category_name or "business" in category_name:
            digital["dominant_app_category"] = "WORK"
        elif "entertainment" in category_name or "video" in category_name:
            digital["dominant_app_category"] = "ENTERTAINMENT"
        else:
            digital["dominant_app_category"] = "UTILITY"
    else:
        digital["dominant_app_category"] = "UTILITY"
    
    result["digital_hygiene"] = digital
    
    return result


# Main execution
# Parse the input JSON string
data = json.loads(filtered_data)

# Categorize physiological and digital data
physiological_digital_dict = categorize_physiological_and_digital(data)

# Convert output to JSON string
physiological_and_digital_status = json.dumps(physiological_digital_dict, indent=2)

physiological_and_digital_status
