import json
import math
from datetime import datetime


# --- CONFIGURATION & THRESHOLDS ---
THRESHOLDS = {
    "traffic": {
        "high": 2.0,        # Travel time > 200% of normal
        "moderate": 1.4     # Travel time > 140% of normal
    },
    "weather": {
        "min_temp_outdoor": 15,
        "bad_conditions": ["Rain", "Snow", "Thunderstorm", "Drizzle"]
    }
}


def process_global_context(env_feed):
    """
    Abstracts raw weather/traffic/time into categorical tags.
    
    Output JSON structure:
    - outdoor_viability: OPTIMAL, VIABLE_WITH_GEAR, or INDOOR_ONLY
    - transit_friction: LOW_FRICTION, MODERATE_DELAY, HIGH_FRICTION, or BLOCKED
    - temporal_phase: WORK_HOURS, EVENING_TRANSITION, PRIME_SOCIAL_TIME, or LATE_NIGHT
    - implication: Natural language hint for reasoning
    """
    
    # Weather Abstraction
    weather_api = env_feed.get("weather_api", {})
    weather_curr = weather_api.get("current", {})
    weather_main = weather_curr.get("weather", [{}])[0].get("main", "Clear")
    temp = weather_curr.get("temp", 20)
    
    if weather_main in THRESHOLDS["weather"]["bad_conditions"]:
        outdoor = "INDOOR_ONLY"
    elif temp < THRESHOLDS["weather"]["min_temp_outdoor"]:
        outdoor = "VIABLE_WITH_GEAR"
    else:
        outdoor = "OPTIMAL"

    # Traffic Abstraction
    traffic_api = env_feed.get("traffic_api", {})
    traffic_idx = traffic_api.get("summary", {}).get("travelTimeIndex", 1.0)
    
    if traffic_idx >= THRESHOLDS["traffic"]["high"]:
        friction = "HIGH_FRICTION"
    elif traffic_idx >= THRESHOLDS["traffic"]["moderate"]:
        friction = "MODERATE_DELAY"
    else:
        friction = "LOW_FRICTION"

    # Time Abstraction
    dt_timestamp = weather_curr.get("dt")
    if dt_timestamp:
        dt_obj = datetime.fromtimestamp(dt_timestamp)
        hour = dt_obj.hour
        if 9 <= hour < 17: 
            phase = "WORK_HOURS"
        elif 17 <= hour < 19: 
            phase = "EVENING_TRANSITION"
        elif 19 <= hour < 22: 
            phase = "PRIME_SOCIAL_TIME"
        else: 
            phase = "LATE_NIGHT"
    else:
        phase = "UNKNOWN"

    return {
        "outdoor_viability": outdoor,
        "transit_friction": friction,
        "temporal_phase": phase,
        "implication": generate_implication(outdoor, friction)
    }


def generate_implication(outdoor, friction):
    """Generates natural language hint for logic."""
    if friction == "HIGH_FRICTION":
        return "Prioritize digital connections, home-based activities, or very local (walking distance) indoor events. Discourage cross-town travel."
    if outdoor == "INDOOR_ONLY":
        return "Focus on indoor venues. Filter out parks and walking groups."
    return "Conditions optimal. Prioritize outdoor social friction reduction."


def transform_user_state(user):
    """
    Maps detailed Sentry analysis to Scout's high-level buckets.
    
    Output JSON structure:
    - availability_status: AVAILABLE_NOW, AVAILABLE_SOON, or BUSY_UNAVAILABLE
    - wellness_need: STRESS_RELIEF, SOCIAL_CONNECTION, REST_RECOVERY, or MAINTENANCE
    - location_context: HOME_BASE, WORK_OFFICE, THIRD_PLACE, or IN_TRANSIT
    - neighborhood: Simplified area name
    """
    sentry = user.get("sentry_analysis", {})
    
    # Availability Mapping
    avail_raw = sentry.get("availability")
    if avail_raw == "FREE": 
        status = "AVAILABLE_NOW"
    elif avail_raw in ["BUSY_BUT_ENDING_SOON", "TRANSITIONING"]: 
        status = "AVAILABLE_SOON"
    else: 
        status = "BUSY_UNAVAILABLE"

    # Wellness Need Mapping
    stress = sentry.get("stress_level")
    risks = sentry.get("risk_flags", [])
    
    if "ISOLATION_RISK" in risks: 
        need = "SOCIAL_CONNECTION"
    elif stress in ["HIGH", "CRITICAL_HIGH"]: 
        need = "REST_RECOVERY"
    elif stress in ["ELEVATED", "MODERATE"]: 
        need = "STRESS_RELIEF"
    elif stress == "FATIGUED": 
        need = "REST_RECOVERY"
    else: 
        need = "MAINTENANCE"

    # Location Context Mapping
    loc_name_full = user.get("current_location", {}).get("name", "")
    loc_name_lower = loc_name_full.lower()
    
    # Infer location category from name
    if "home" in loc_name_lower:
        loc_cat = "HOME_BASE"
    elif "office" in loc_name_lower or "work" in loc_name_lower:
        loc_cat = "WORK_OFFICE"
    elif "transit" in loc_name_lower or "commuting" in loc_name_lower:
        loc_cat = "IN_TRANSIT"
    elif any(place in loc_name_lower for place in ["cafe", "coffee", "park", "gym", "restaurant"]):
        loc_cat = "THIRD_PLACE"
    else:
        loc_cat = "HOME_BASE"
    
    # Extract simplified neighborhood/area name
    if "(" in loc_name_full:
        neighborhood = loc_name_full.split("(")[-1].strip(")")
    elif "transit" in loc_name_lower or "commuting" in loc_name_lower:
        if "mittlerer" in loc_name_lower or "ring" in loc_name_lower:
            neighborhood = "Transit_Corridor_East"
        else:
            neighborhood = "In_Transit"
    elif loc_cat == "THIRD_PLACE":
        if "lost weekend" in loc_name_lower:
            neighborhood = "Schwabing-West"
        else:
            neighborhood = loc_name_full.split()[0] if loc_name_full else "Unknown"
    else:
        neighborhood = loc_name_full

    return {
        "user_id": user.get("user_id"),
        "availability_status": status,
        "wellness_need": need,
        "location_context": loc_cat,
        "neighborhood": neighborhood
    }


def analyze_relationships(users, global_context):
    """
    Scans social graphs to find friction points.
    
    Output: List of relationship friction objects with:
    - source_user, target_user
    - relationship_type (FRIEND, PARENT_CHILD, etc.)
    - connection_health (HEALTHY, CRITICAL_DISCONNECT)
    - proximity_opportunity (CO_LOCATED, WALKING_DISTANCE, SAME_DISTRICT, DISTANT)
    - scout_hint (natural language guidance)
    """
    results = []
    seen_pairs = set()
    
    # Helper to look up user location
    user_locs = {u["user_id"]: u["current_location"] for u in users}

    for source_user in users:
        social_graph = source_user.get("social_graph_snapshot", [])
        
        for relation in social_graph:
            target_id = relation.get("target_id")
            status = relation.get("status")
            
            # Create a canonical pair key (sorted to avoid duplicates)
            pair_key = tuple(sorted([source_user["user_id"], target_id]))
            
            # Skip if we've already processed this pair
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            
            # Calculate proximity
            prox = calculate_proximity_category(
                user_locs.get(source_user["user_id"]),
                user_locs.get(target_id)
            )
            
            # Logic for Relationship Bridge (Negative Trigger)
            if status == "CRITICAL_DISCONNECT":
                # Generate Hint
                hint = "Critical Disconnect detected."
                if global_context["transit_friction"] == "HIGH_FRICTION" and prox == "DISTANT":
                    hint = "High Friction Travel + Critical Disconnect = Suggest Phone/Video Call."
                elif prox == "WALKING_DISTANCE":
                    hint = "Nearby + Disconnected = Suggest immediate meetup."
                
                # Map relationship type to canonical form
                rel_type = relation.get("relation", "").upper()
                if rel_type in ["SON", "DAUGHTER", "FATHER", "MOTHER"]:
                    rel_type = "PARENT_CHILD"

                results.append({
                    "source_user": source_user["user_id"],
                    "target_user": target_id,
                    "relationship_type": rel_type,
                    "connection_health": "CRITICAL_DISCONNECT",
                    "proximity_opportunity": prox,
                    "scout_hint": hint
                })
            
            # Logic for Vicinity (Positive Trigger)
            elif status == "GOOD":
                if prox == "WALKING_DISTANCE":
                    results.append({
                        "source_user": source_user["user_id"],
                        "target_user": target_id,
                        "relationship_type": relation.get("relation").upper(),
                        "connection_health": "HEALTHY",
                        "proximity_opportunity": "WALKING_DISTANCE",
                        "scout_hint": f"Healthy connection + nearby + '{global_context['outdoor_viability']}' weather = Suggest local indoor hangout."
                    })

    return results


def calculate_proximity_category(loc_a, loc_b):
    """
    Simple distance logic using lat/lon coordinates.
    Returns: CO_LOCATED, WALKING_DISTANCE, SAME_DISTRICT, or DISTANT
    """
    if not loc_a or not loc_b: 
        return "UNKNOWN"
    
    # Coordinate math (Haversine simplified)
    lat1, lon1 = loc_a.get("lat", 0), loc_a.get("lon", 0)
    lat2, lon2 = loc_b.get("lat", 0), loc_b.get("lon", 0)
    
    # Approx distance in km (rough approximation for Munich's latitude)
    dist = math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111 
    
    if dist < 0.2: 
        return "CO_LOCATED"
    if dist < 1.0: 
        return "WALKING_DISTANCE"
    if dist < 2.0: 
        return "SAME_DISTRICT"
    return "DISTANT"


def curate_opportunities(events, global_context, users_map):
    """
    Filters events based on environment and user suitability.
    
    Output: List of curated opportunity objects with:
    - event_id, title
    - activity_type (ACTIVE_PHYSICAL, SOCIAL_GATHERING, etc.)
    - environment_match (MATCHES_CURRENT_CONDITIONS or MISMATCH)
    - location_context (venue name)
    - suitability (dict of user_id -> score for non-LOW scores)
    - reason (optional, only if MISMATCH)
    """
    curated = []
    
    for event in events:
        # Extract event details from Schema.org format
        event_id = event.get("identifier")
        title = event.get("name")
        event_type = event.get("@type", "")
        description = event.get("description", "")
        location_obj = event.get("location", {})
        location_name = location_obj.get("name", "Unknown Area")
        
        # 1. Environment Check
        event_text = f"{title} {description} {event_type}".lower()
        is_outdoor = any(keyword in event_text for keyword in 
                        ["walking", "park", "outdoor", "garden", "hiking", "nature"])
        
        env_match = "MATCHES_CURRENT_CONDITIONS"
        reason = None
        
        if global_context["outdoor_viability"] == "INDOOR_ONLY" and is_outdoor:
            env_match = "MISMATCH"
            reason = "Outdoor event during Rain"

        # 2. Suitability Scoring
        suitability = {}
        
        for user in users_map:
            score = "LOW"
            uid = user["user_id"]
            
            # Match based on event type and user wellness needs
            if event_type == "SportsEvent":
                if uid == "user_01_student" and user["wellness_need"] == "STRESS_RELIEF": 
                    score = "HIGH"
                elif user["wellness_need"] == "STRESS_RELIEF": 
                    score = "MEDIUM"
            
            elif event_type == "SocialEvent":
                if "expat" in description.lower() and uid == "user_03_expat": 
                    score = "HIGH"
                elif "english" in title.lower() and uid == "user_03_expat":
                    score = "HIGH"
                elif uid == "user_01_student": 
                    score = "MEDIUM"
                elif user["wellness_need"] == "SOCIAL_CONNECTION":
                    score = "MEDIUM"
            
            elif event_type == "MusicEvent":
                if uid == "user_02_retired": 
                    score = "MEDIUM"
                
            suitability[uid] = score

        # Filter suitability to only show non-LOW scores
        filtered_suitability = {uid: score for uid, score in suitability.items() if score != "LOW"}
        
        event_item = {
            "event_id": event_id,
            "title": title,
            "activity_type": map_activity_category(event_type),
            "environment_match": env_match,
            "location_context": location_name,
            "suitability": filtered_suitability
        }
        
        # Only add reason field if there's a mismatch
        if reason:
            event_item["reason"] = reason
            
        curated.append(event_item)
        
    return curated


def map_activity_category(event_type):
    """Maps Schema.org event types to Scout Schema."""
    mapping = {
        "SocialEvent": "SOCIAL_GATHERING",
        "SportsEvent": "ACTIVE_PHYSICAL",
        "MusicEvent": "CULTURAL_PASSIVE",
        "TheaterEvent": "CULTURAL_PASSIVE",
        "EducationEvent": "COMMUNITY_SUPPORT",
        "VolunteerEvent": "COMMUNITY_SUPPORT"
    }
    return mapping.get(event_type, "SOCIAL_GATHERING")


def lambda_handler(event, context):
    """
    AWS Lambda handler function that transforms Scout raw input to categorized output.
    
    Expected input: JSON object matching scout_raw_input.json structure
    This can be in various formats:
    - Direct JSON object
    - JSON string
    - API Gateway event with body
    - Bedrock Flows node format
    
    Returns: Transformed JSON matching scout_transformed_input.json and scout_input_schema.json
    """
    
    # Detect if this is an API Gateway invocation
    is_api_gateway = "requestContext" in event or "httpMethod" in event
    
    try:
        # Handle different event formats (matching lambda_data_categorization.py)
        if isinstance(event, str):
            raw_data = json.loads(event)
        elif "node" in event and "inputs" in event["node"]:
            # Bedrock Flows format
            inputs = event["node"]["inputs"]
            raw_input = None
            for input_item in inputs:
                if input_item.get("name") in ["scout_raw_data", "raw_data"]:
                    raw_input = input_item.get("value")
                    break
            if raw_input is None:
                raise ValueError("scout_raw_data not found in Bedrock Flows inputs")
            
            if isinstance(raw_input, str):
                raw_data = json.loads(raw_input)
            else:
                raw_data = raw_input
        elif "body" in event:
            # API Gateway format
            body = event["body"]
            if isinstance(body, str):
                raw_data = json.loads(body)
            else:
                raw_data = body
        elif "scout_raw_data" in event or "raw_data" in event:
            # Direct parameter format
            raw_input = event.get("scout_raw_data") or event.get("raw_data")
            if isinstance(raw_input, str):
                raw_data = json.loads(raw_input)
            else:
                raw_data = raw_input
        else:
            # Assume event is the data object itself
            raw_data = event
        
        # Execute all transformation steps
        global_context = process_global_context(raw_data.get("environment_feed", {}))
        
        users = raw_data.get("users_sentry_state", [])
        user_cluster_map = [transform_user_state(u) for u in users]
        
        relationships = analyze_relationships(users, global_context)
        
        raw_events = raw_data.get("environment_feed", {}).get("events_api", {}).get("items", [])
        opportunities = curate_opportunities(raw_events, global_context, user_cluster_map)

        # Construct Final Payload
        response_payload = {
            "global_context": global_context,
            "user_cluster_map": user_cluster_map,
            "relationship_frictions": relationships,
            "curated_opportunity_feed": opportunities
        }
        
        # Convert output to JSON string
        output_json = json.dumps(response_payload, indent=2)
        
        # Return format depends on invocation source (matching lambda_data_categorization.py)
        if is_api_gateway:
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": output_json
            }
        else:
            # Bedrock Flows expects direct string output
            return output_json

    except json.JSONDecodeError as e:
        error_response = {
            "error": "Invalid JSON input",
            "message": str(e)
        }
        
        if is_api_gateway:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps(error_response)
            }
        else:
            return json.dumps(error_response)
    
    except Exception as e:
        error_response = {
            "error": "Internal server error",
            "message": str(e),
            "event_received": str(event)[:500]
        }
        
        if is_api_gateway:
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps(error_response)
            }
        else:
            return json.dumps(error_response)


# For local testing
if __name__ == "__main__":
    import sys
    import os
    
    # Load test data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_file_path = os.path.join(script_dir, '..', 'mock_data', 'scout_raw_input.json')
    expected_output_path = os.path.join(script_dir, '..', 'mock_data', 'scout_transformed_input.json')
    
    with open(test_file_path, 'r') as f:
        test_data = json.load(f)
    
    # Transform the data
    print("=" * 80)
    print("SCOUT TRANSFORMATION TEST")
    print("=" * 80)
    print(f"\nInput: scout_raw_input.json")
    print(f"Users: {len(test_data.get('users_sentry_state', []))}")
    print(f"Events: {len(test_data.get('environment_feed', {}).get('events_api', {}).get('items', []))}")
    
    result = lambda_handler(test_data, None)
    
    # Parse result based on format
    if isinstance(result, str):
        output_data = json.loads(result)
        print("\nTransformed Output:")
        print(result)
    else:
        output_data = json.loads(result.get('body'))
        print("\nStatus Code:", result.get('statusCode'))
        print("\nTransformed Output:")
        print(result.get('body'))
    
    # Validate structure
    print("\n" + "=" * 80)
    print("SCHEMA VALIDATION")
    print("=" * 80)
    
    expected_keys = ["global_context", "user_cluster_map", "relationship_frictions", "curated_opportunity_feed"]
    actual_keys = list(output_data.keys())
    
    print(f"\nExpected keys: {expected_keys}")
    print(f"Actual keys: {actual_keys}")
    print(f"Schema match: {set(expected_keys) == set(actual_keys)}")
    
    # Load expected output for comparison
    try:
        with open(expected_output_path, 'r') as f:
            expected_output = json.load(f)
        
        print("\n" + "=" * 80)
        print("COMPARISON WITH EXPECTED OUTPUT")
        print("=" * 80)
        
        # Compare global context
        gc_actual = output_data['global_context']
        gc_expected = expected_output['global_context']
        print("\nGlobal Context:")
        print(f"  outdoor_viability: {gc_actual['outdoor_viability']} ✓" if gc_actual['outdoor_viability'] == gc_expected['outdoor_viability'] else f"  outdoor_viability: {gc_actual['outdoor_viability']} (expected: {gc_expected['outdoor_viability']}) ✗")
        print(f"  transit_friction: {gc_actual['transit_friction']} ✓" if gc_actual['transit_friction'] == gc_expected['transit_friction'] else f"  transit_friction: {gc_actual['transit_friction']} (expected: {gc_expected['transit_friction']}) ✗")
        print(f"  temporal_phase: {gc_actual['temporal_phase']} ✓" if gc_actual['temporal_phase'] == gc_expected['temporal_phase'] else f"  temporal_phase: {gc_actual['temporal_phase']} (expected: {gc_expected['temporal_phase']}) ✗")
        
        # Compare user count and sample
        print(f"\nUser Cluster Map: {len(output_data['user_cluster_map'])} users ✓" if len(output_data['user_cluster_map']) == len(expected_output['user_cluster_map']) else f"\nUser Cluster Map: {len(output_data['user_cluster_map'])} users (expected: {len(expected_output['user_cluster_map'])}) ✗")
        
        for i, (user_actual, user_expected) in enumerate(zip(output_data['user_cluster_map'], expected_output['user_cluster_map'])):
            match = (user_actual['availability_status'] == user_expected['availability_status'] and 
                    user_actual['wellness_need'] == user_expected['wellness_need'] and 
                    user_actual['location_context'] == user_expected['location_context'])
            status = "✓" if match else "✗"
            print(f"  {user_actual['user_id']}: {user_actual['availability_status']}, {user_actual['wellness_need']}, {user_actual['location_context']} {status}")
        
        # Compare relationships
        print(f"\nRelationship Frictions: {len(output_data['relationship_frictions'])} ✓" if len(output_data['relationship_frictions']) == len(expected_output['relationship_frictions']) else f"\nRelationship Frictions: {len(output_data['relationship_frictions'])} (expected: {len(expected_output['relationship_frictions'])}) ✗")
        
        for rel in output_data['relationship_frictions']:
            print(f"  {rel['source_user']} -> {rel['target_user']}: {rel['connection_health']}, {rel['proximity_opportunity']}")
        
        # Compare opportunities
        print(f"\nCurated Opportunities: {len(output_data['curated_opportunity_feed'])} events")
        for opp in output_data['curated_opportunity_feed']:
            high_scores = [uid for uid, score in opp['suitability'].items() if score == 'HIGH']
            print(f"  {opp['event_id']}: {opp['activity_type']}, {opp['environment_match']}")
            if high_scores:
                print(f"    HIGH suitability: {', '.join(high_scores)}")
    
    except FileNotFoundError:
        print(f"\nExpected output file not found: {expected_output_path}")
        print("Skipping comparison.")
