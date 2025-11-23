import json
from datetime import datetime


def categorize_user_profile(filtered_data):
    """
    Extracts and categorizes user profile information from filtered stress data.
    
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


def categorize_physiological_and_digital(filtered_data):
    """
    Extracts and categorizes physiological state and digital hygiene from filtered stress data.
    
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


def categorize_spatial_and_schedule(filtered_data):
    """
    Extracts and categorizes spatial context and schedule context from filtered stress data.
    
    Output JSON structure:
    - spatial_context:
        - location_category: HOME, WORK_UNIVERSITY, THIRD_PLACE, NATURE, or TRANSIT
        - mobility_mode: STATIONARY, WALKING, DRIVING, or CYCLING
        - social_environment_inferred: SOLITARY, CROWDED_PUBLIC, or PRIVATE_GROUP
    - schedule_context:
        - current_availability: FREE, BUSY, or TRANSITION_BUFFER
        - upcoming_event_type: NONE, SOCIAL, WORK_ACADEMIC, MEDICAL, or LOGISTICAL
        - schedule_density: OPEN_DAY, BALANCED, or PACKED_DAY
    """
    result = {}
    
    # ========== SPATIAL CONTEXT ==========
    spatial = {}
    
    # Analyze location patterns
    location = filtered_data.get("location_patterns", {})
    current_location = (location.get("current_location") or "").lower()
    home_time = location.get("home_time_hours", 0)
    places_visited = location.get("total_places_visited", 0)
    
    # Categorize location_category
    if "home" in current_location:
        spatial["location_category"] = "HOME"
    elif "university" in current_location or "office" in current_location or "work" in current_location:
        spatial["location_category"] = "WORK_UNIVERSITY"
    elif "park" in current_location or "garden" in current_location or "nature" in current_location or "englischer garten" in current_location:
        spatial["location_category"] = "NATURE"
    elif "cafe" in current_location or "restaurant" in current_location or "bar" in current_location or "coffee" in current_location or "roasters" in current_location:
        spatial["location_category"] = "THIRD_PLACE"
    else:
        spatial["location_category"] = "TRANSIT"
    
    # Categorize mobility_mode (simplified - could be enhanced with activity segment data)
    if places_visited <= 1:
        spatial["mobility_mode"] = "STATIONARY"
    else:
        spatial["mobility_mode"] = "WALKING"  # Default assumption
    
    # Categorize social_environment_inferred
    if home_time > 20:  # More than 20 hours at home
        spatial["social_environment_inferred"] = "SOLITARY"
    elif "cafe" in current_location or "restaurant" in current_location or "coffee" in current_location or "roasters" in current_location or "bar" in current_location:
        spatial["social_environment_inferred"] = "CROWDED_PUBLIC"
    else:
        spatial["social_environment_inferred"] = "SOLITARY"
    
    result["spatial_context"] = spatial
    
    # ========== SCHEDULE CONTEXT ==========
    schedule = {}
    
    # Analyze upcoming events
    events = filtered_data.get("upcoming_events", [])
    
    # Categorize current_availability
    if not events:
        schedule["current_availability"] = "FREE"
    else:
        # Check if first event is soon (within 1 hour)
        first_event = events[0] if events else None
        if first_event:
            start_time_str = first_event.get("start")
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                    now = datetime.now(start_time.tzinfo)
                    time_until = (start_time - now).total_seconds() / 3600
                    
                    if time_until < 0:
                        schedule["current_availability"] = "BUSY"
                    elif time_until < 1:
                        schedule["current_availability"] = "TRANSITION_BUFFER"
                    else:
                        schedule["current_availability"] = "FREE"
                except (ValueError, AttributeError):
                    schedule["current_availability"] = "FREE"
            else:
                schedule["current_availability"] = "FREE"
        else:
            schedule["current_availability"] = "FREE"
    
    # Categorize upcoming_event_type
    if not events:
        schedule["upcoming_event_type"] = "NONE"
    else:
        first_event = events[0]
        summary = first_event.get("summary", "").lower()
        
        if "exam" in summary or "test" in summary or "work" in summary or "meeting" in summary:
            schedule["upcoming_event_type"] = "WORK_ACADEMIC"
        elif "doctor" in summary or "medical" in summary or "health" in summary or "appointment" in summary:
            schedule["upcoming_event_type"] = "MEDICAL"
        elif "coffee" in summary or "lunch" in summary or "dinner" in summary or "party" in summary:
            schedule["upcoming_event_type"] = "SOCIAL"
        elif "flight" in summary or "train" in summary or "travel" in summary:
            schedule["upcoming_event_type"] = "LOGISTICAL"
        else:
            schedule["upcoming_event_type"] = "SOCIAL"
    
    # Categorize schedule_density
    events_count = len(events)
    if events_count == 0:
        schedule["schedule_density"] = "OPEN_DAY"
    elif events_count <= 3:
        schedule["schedule_density"] = "BALANCED"
    else:
        schedule["schedule_density"] = "PACKED_DAY"
    
    result["schedule_context"] = schedule
    
    return result


def aggregate_categorizations(user_profile, physiological_digital, spatial_schedule):
    """
    Aggregates categorized data from three categorization functions into final JSON structure.
    
    Output JSON structure matches sentry_input_schema.json:
    - user_profile: Static user attributes
    - physiological_state: Bio-data categories
    - digital_hygiene: Device usage patterns
    - spatial_context: Location-based context
    - schedule_context: Calendar-based availability
    """
    aggregated = {
        "user_profile": user_profile,
        "physiological_state": physiological_digital.get("physiological_state", {}),
        "digital_hygiene": physiological_digital.get("digital_hygiene", {}),
        "spatial_context": spatial_schedule.get("spatial_context", {}),
        "schedule_context": spatial_schedule.get("schedule_context", {})
    }
    
    return aggregated


def lambda_handler(event, context):
    """
    AWS Lambda handler function that processes the filtered data from lambda_data_filtering.py
    and returns aggregated categorized output.
    
    Expected input: Filtered stress indicator data (output from lambda_data_filtering.py)
    This can be in various formats:
    - Direct JSON string from lambda_data_filtering.py
    - API Gateway event with body
    - Bedrock Flows node format
    - Direct JSON object
    
    Returns: Aggregated categorized JSON matching sentry_input_schema.json
    """
    
    # Detect if this is an API Gateway invocation
    is_api_gateway = "requestContext" in event or "httpMethod" in event
    
    try:
        # Handle different event formats (matching lambda_data_filtering.py)
        if isinstance(event, str):
            # Event is already a JSON string
            filtered_data = json.loads(event)
        elif "node" in event and "inputs" in event["node"]:
            # Bedrock Flows format
            inputs = event["node"]["inputs"]
            filtered_input = None
            for input_item in inputs:
                if input_item.get("name") in ["filtered_data", "stress_indicators"]:
                    filtered_input = input_item.get("value")
                    break
            if filtered_input is None:
                raise ValueError("filtered_data or stress_indicators not found in Bedrock Flows inputs")
            
            if isinstance(filtered_input, str):
                filtered_data = json.loads(filtered_input)
            else:
                filtered_data = filtered_input
        elif "body" in event:
            # API Gateway format
            body = event["body"]
            if isinstance(body, str):
                filtered_data = json.loads(body)
            else:
                filtered_data = body
        elif "filtered_data" in event:
            # Direct parameter format
            filtered_input = event["filtered_data"]
            if isinstance(filtered_input, str):
                filtered_data = json.loads(filtered_input)
            else:
                filtered_data = filtered_input
        else:
            # Assume event is the data object itself
            filtered_data = event
        
        # Execute all categorization steps
        user_profile_data = categorize_user_profile(filtered_data)
        physiological_digital_data = categorize_physiological_and_digital(filtered_data)
        spatial_schedule_data = categorize_spatial_and_schedule(filtered_data)
        
        # Aggregate all categorizations
        aggregated_result = aggregate_categorizations(
            user_profile_data,
            physiological_digital_data,
            spatial_schedule_data
        )
        
        # Convert output to JSON string
        output_json = json.dumps(aggregated_result, indent=2)
        
        # Return format depends on invocation source (matching lambda_data_filtering.py)
        if is_api_gateway:
            # API Gateway expects HTTP response format
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': output_json
            }
        else:
            # Bedrock Flows expects direct string output
            return output_json
        
    except json.JSONDecodeError as e:
        error_response = {
            'error': 'Invalid JSON input',
            'message': str(e)
        }
        
        if is_api_gateway:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps(error_response)
            }
        else:
            return json.dumps(error_response)
        
    except Exception as e:
        error_response = {
            'error': 'Internal server error',
            'message': str(e),
            'event_received': str(event)[:500]  # Include first 500 chars for debugging
        }
        
        if is_api_gateway:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps(error_response)
            }
        else:
            return json.dumps(error_response)


# For local testing
if __name__ == "__main__":
    import sys
    import os
    
    # Add parent directory to path to import lambda_data_filtering
    sys.path.insert(0, os.path.dirname(__file__))
    from lambda_data_filtering import extract_stress_indicators
    
    # Load test data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_file_path = os.path.join(script_dir, '..', '..', 'mock_data', 'sentry_input_test_01_retired_person.json')
    with open(test_file_path, 'r') as f:
        test_data = json.load(f)
    
    # First, filter the data (simulate lambda_data_filtering.py output)
    print("=" * 80)
    print("STEP 1: Filtering data (lambda_data_filtering.py)")
    print("=" * 80)
    filtered_data = extract_stress_indicators(test_data)
    filtered_json = json.dumps(filtered_data, indent=2)
    print("\nFiltered data keys:", list(filtered_data.keys()))
    
    # Then, categorize the filtered data
    print("\n" + "=" * 80)
    print("STEP 2: Categorizing data (lambda_data_categorization.py)")
    print("=" * 80)
    result = lambda_handler(filtered_json, None)
    
    # Parse result based on format
    if isinstance(result, str):
        # Bedrock Flows format
        print("\nCategorized Output (JSON):")
        print(result)
    else:
        # API Gateway format
        print("\nStatus Code:", result.get('statusCode'))
        print("\nCategorized Output:")
        print(result.get('body'))
    
    # Validate against schema
    print("\n" + "=" * 80)
    print("SCHEMA VALIDATION")
    print("=" * 80)
    
    output_data = json.loads(result if isinstance(result, str) else result.get('body'))
    
    expected_keys = ["user_profile", "physiological_state", "digital_hygiene", "spatial_context", "schedule_context"]
    actual_keys = list(output_data.keys())
    
    print(f"\nExpected keys: {expected_keys}")
    print(f"Actual keys: {actual_keys}")
    print(f"Schema match: {set(expected_keys) == set(actual_keys)}")
    
    # Check each category
    schema_path = os.path.join(script_dir, 'schemas', 'sentry_input_schema.json')
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    for category in expected_keys:
        if category in output_data:
            print(f"\n{category}:")
            for field, value in output_data[category].items():
                # Check if value is in allowed values
                allowed = schema['definitions'][category]['fields'].get(field, [])
                is_valid = value in allowed if allowed else "N/A"
                print(f"  - {field}: {value} (valid: {is_valid})")
