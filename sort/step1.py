import os
import json
import argparse

source_dir = "./temp/data"
parser = argparse.ArgumentParser()
parser.add_argument("--target-dir", type=str, required=True)
args = parser.parse_args()
target_dir = args.target_dir
mutual_unfollow_path = os.path.join(source_dir, "mutual_unfollow.txt")

with open(mutual_unfollow_path, 'w', encoding='utf-8') as mutual_unfollow_file:
    for filename in os.listdir(target_dir):
        if filename.endswith('.json'):
            target_file_path = os.path.join(target_dir, filename)
            source_file_path = os.path.join(source_dir, filename)

            if not os.path.exists(source_file_path):
                try:
                    with open(target_file_path, 'r', encoding='utf-8') as target_file:
                        data = json.load(target_file)
                        if 'id' in data and isinstance(data['id'], str):
                            mutual_unfollow_file.write(f"{data['id']}\n")
                        else:
                            print(f"'id' is missing or not a valid string in file: {target_file_path}")
                except json.JSONDecodeError:
                    print(f"Error decoding JSON in file: {target_file_path}")
