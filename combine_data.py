'''
This script combines all the data from the extracted folder into a single JSON file - output.json
'''

import os
import json

input_folder = 'extracted'
output_file = 'output.json'

combined_data = []

for subfolder in os.listdir(input_folder):
    subfolder_path = os.path.join(input_folder, subfolder)
    
    if os.path.isdir(subfolder_path):
        for json_file in os.listdir(subfolder_path):
            if json_file.startswith('PAGE_') and json_file.endswith('.json'):
                json_file_path = os.path.join(subfolder_path, json_file)
                
                with open(json_file_path, 'r') as f:
                    json_data = json.load(f)
                    combined_data.extend(data for data in json_data if data.get('full_text') != '')
                    
with open(output_file, 'w') as f:
    json.dump(combined_data, f, indent=2)

print(f"Total items in output.json: {len(combined_data)}")
