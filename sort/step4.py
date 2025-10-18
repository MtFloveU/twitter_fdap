import os
import json
import argparse

source_dir = "./temp/data"
parser = argparse.ArgumentParser()
parser.add_argument("--target-dir", type=str, required=True)
args = parser.parse_args()
target_dir = args.target_dir
single_unfollower_path = os.path.join(source_dir, "single-unfollower-return.txt")
unfollower_txt_path = os.path.join(source_dir, "single-unfollower.txt")

with open(unfollower_txt_path, 'r', encoding='utf-8') as f:
    unfollower_ids = set(line.strip() for line in f)

with open(single_unfollower_path, 'w', encoding='utf-8') as single_unfollower_file:
    for filename in os.listdir(target_dir):
        if filename.endswith('.json'):
            target_file_path = os.path.join(target_dir, filename)
            source_file_path = os.path.join(source_dir, filename)
            if os.path.isfile(source_file_path):
                with open(target_file_path, 'r', encoding='utf-8') as target_file:
                    target_data = json.load(target_file)
                with open(source_file_path, 'r', encoding='utf-8') as source_file:
                    source_data = json.load(source_file)
                if str(source_data.get('id')) in unfollower_ids and str(source_data.get('followed_by')) == "True" and str(source_data.get('following')) == "True":
                    single_unfollower_file.write(f"{target_data['id']}\n")
