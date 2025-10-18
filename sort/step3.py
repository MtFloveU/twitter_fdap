import os
import json
import argparse

source_dir = "./temp/data"
parser = argparse.ArgumentParser()
parser.add_argument("--target-dir", type=str, required=True)
args = parser.parse_args()
target_dir = args.target_dir
single_unfollowing_path = os.path.join(source_dir, "single-unfollowing.txt")

with open(single_unfollowing_path, 'w', encoding='utf-8') as single_unfollowing_file:
    for filename in os.listdir(target_dir):
        if filename.endswith('.json'):
            target_file_path = os.path.join(target_dir, filename)
            source_file_path = os.path.join(source_dir, filename)

            if os.path.isfile(source_file_path):
                try:
                    with open(target_file_path, 'r', encoding='utf-8') as target_file:
                        target_data = json.load(target_file)
                    with open(source_file_path, 'r', encoding='utf-8') as source_file:
                        source_data = json.load(source_file)

                    following_target = str(target_data.get('following'))
                    following_source = str(source_data.get('following'))

                    if following_target == "True" and (following_source == "None" or following_source == "False"):
                        single_unfollowing_file.write(f"{target_data['id']}\n")

                except json.JSONDecodeError:
                    print(f"Error decoding JSON in file: {target_file_path} or {source_file_path}")
                except KeyError:
                    print(f"Key 'id' not found in file: {target_file_path} or {source_file_path}")
