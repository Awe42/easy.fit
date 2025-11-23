import json

comb_dict = json.loads(combined_input)
scout_raw_data = comb_dict["scout"]
scout_raw_data = json.dumps(scout_raw_data)

scout_raw_data