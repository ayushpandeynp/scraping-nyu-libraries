'''
This script is used to calculate the basic statistics of the dataset.
'''

import json
import os

data_folder = 'data-compressed'
output_folder = 'extracted'
statistics = {"pdf_total": 0, "html_total": 0,
              "html_with_full_text": 0, "pdf_with_full_text": 0}

os.makedirs(output_folder, exist_ok=True)

for compressed_file in os.listdir(data_folder):
    if compressed_file.endswith('.zip'):
        base_name = os.path.splitext(compressed_file)[0]
        output_subfolder = os.path.join(output_folder, base_name)
        os.makedirs(output_subfolder, exist_ok=True)

        os.system(
            f'tar -xf {os.path.join(data_folder, compressed_file)} -C {output_subfolder}')

for ex_folder in os.listdir(output_folder):
    ex_folder_path = os.path.join(output_folder, ex_folder)
    if os.path.isdir(ex_folder_path):
        for json_file in os.listdir(ex_folder_path):
            if json_file.endswith('.json'):
                with open(os.path.join(ex_folder_path, json_file), 'r') as f:
                    json_data = json.load(f)

                    for data in json_data:
                        file_type = data['html/pdf']
                        statistics[file_type + '_total'] += 1

                        if data['full_text']:
                            statistics[file_type + '_with_full_text'] += 1

print(statistics)
