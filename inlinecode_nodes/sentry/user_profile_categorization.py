import json

def categorize_user_profile(filtered_data):
    """
    Extracts and categorizes user profile information from filtered stress data.
    
    Input: filtered_data - JSON object containing stress indicators from data_filtering.py
    
    Output JSON structure:
    - life_stage: STUDENT, PROFESSIONAL, RETIRED, or EXPAT
    - mobility_profile: UNRESTRICTED, MODERATE, or LIMITED_MOBILITY
    - social_battery_preference: MORNING_PERSON, NIGHT_OWL, or ALWAYS_ON
    - communication_style: CASUAL_BUDDY, FORMAL_EMPATHETIC, or STRICT_COACH
    - intervention_level: PASSIVE, SUGGESTIVE, or ASSERTIVE
    """
    
    user_profile = {}
    
    # Determine life_stage from occupation
    occupation = filtered_data.get("occupation", "").lower()
    if "student" in occupation or "university" in occupation:
        user_profile["life_stage"] = "STUDENT"
    elif "retired" in occupation or "pension" in occupation:
        user_profile["life_stage"] = "RETIRED"
    elif "expat" in occupation or "expatriate" in occupation:
        user_profile["life_stage"] = "EXPAT"
    else:
        user_profile["life_stage"] = "PROFESSIONAL"
    
    # Determine mobility_profile from age and activity levels
    age = filtered_data.get("user_age", 0)
    if age >= 80:
        user_profile["mobility_profile"] = "LIMITED_MOBILITY"
    elif age >= 70:
        user_profile["mobility_profile"] = "MODERATE"
    else:
        user_profile["mobility_profile"] = "UNRESTRICTED"
    
    # Default values for user preferences (can be enhanced with user settings)
    user_profile["social_battery_preference"] = "MORNING_PERSON"
    user_profile["communication_style"] = "FORMAL_EMPATHETIC"
    user_profile["intervention_level"] = "SUGGESTIVE"
    
    return user_profile


# Main execution
# Parse the input JSON string
data = json.loads(filtered_data)

# Categorize user profile
user_profile_dict = categorize_user_profile(data)

# Convert output to JSON string
user_profile_categorization = json.dumps(user_profile_dict, indent=2)

user_profile_categorization
