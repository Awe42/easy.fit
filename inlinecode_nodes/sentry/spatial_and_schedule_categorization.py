import json
from datetime import datetime

def categorize_spatial_and_schedule(filtered_data):
    """
    Extracts and categorizes spatial context and schedule context from filtered stress data.
    
    Input: filtered_data - JSON object containing stress indicators from data_filtering.py
    
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
    current_location = location.get("current_location", "").lower()
    home_time = location.get("home_time_hours", 0)
    places_visited = location.get("total_places_visited", 0)
    
    # Categorize location_category
    if "home" in current_location:
        spatial["location_category"] = "HOME"
    elif "university" in current_location or "office" in current_location or "work" in current_location:
        spatial["location_category"] = "WORK_UNIVERSITY"
    elif "park" in current_location or "garden" in current_location or "nature" in current_location:
        spatial["location_category"] = "NATURE"
    elif "cafe" in current_location or "restaurant" in current_location or "bar" in current_location:
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
    elif "cafe" in current_location or "restaurant" in current_location:
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


# Main execution
# Parse the input JSON string
data = json.loads(filtered_data)

# Categorize spatial and schedule data
spatial_schedule_dict = categorize_spatial_and_schedule(data)

# Convert output to JSON string
spatial_schedule_context = json.dumps(spatial_schedule_dict, indent=2)

spatial_schedule_context
