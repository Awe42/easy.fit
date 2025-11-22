import json

def aggregate_categorizations(user_profile, physiological_digital, spatial_schedule):
    """
    Aggregates categorized data from three previous nodes into final JSON structure.
    
    Inputs:
    - user_profile: JSON object with life_stage, mobility_profile, etc.
    - physiological_digital: JSON object with physiological_state and digital_hygiene
    - spatial_schedule: JSON object with spatial_context and schedule_context
    
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


# Main execution
# Parse the input JSON strings
user_profile_data = json.loads(user_profile_categorization)
physiological_digital_data = json.loads(physiological_and_digital_status)
spatial_schedule_data = json.loads(spatial_schedule_context)

# Aggregate all categorizations
aggregated_dict = aggregate_categorizations(
    user_profile_data,
    physiological_digital_data,
    spatial_schedule_data
)

# Convert output to JSON string
output_data = json.dumps(aggregated_dict, indent=2)

output_data
