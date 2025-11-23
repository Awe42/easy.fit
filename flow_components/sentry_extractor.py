import json

comb_dict = json.loads(combined_input)
sentry_input_data = comb_dict["sentry"]
sentry_input_data = json.dumps(sentry_input_data)

sentry_input_data