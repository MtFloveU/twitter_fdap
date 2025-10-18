import os
import json
import shutil
import argparse
 
source_dir = "./temp/data"
parser = argparse.ArgumentParser()
parser.add_argument("--target-dir", type=str, required=True)
args = parser.parse_args()
target_dir = args.target_dir
removed_list_path = f"{target_dir}/removed_list.txt"

def json_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return {key: data[key] for key in ('screen_name', 'name', 'description', 'followed_by', 'following', 'location')}

with open(removed_list_path, 'r', encoding='utf-8') as removed_list_file:
    removed_list = removed_list_file.read().splitlines()

for filename in os.listdir(source_dir):
    if filename.endswith('.json'):
        source_file_path = os.path.join(source_dir, filename)
        target_file_path = os.path.join(target_dir, filename)

        if os.path.isfile(target_file_path):
            source_data = json_data(source_file_path)
            with open(target_file_path, 'r', encoding='utf-8') as target_file:
                target_data = json.load(target_file)
            target_data = {key: target_data[key] for key in ('screen_name', 'name', 'description', 'followed_by', 'following', 'location')}

            if source_data != target_data:
                shutil.copy2(source_file_path, target_file_path)
        else:
            with open(source_file_path, 'r', encoding='utf-8') as source_file:
                source_id = json.load(source_file).get('id')
            if source_id and source_id not in removed_list:
                shutil.copy2(source_file_path, target_file_path)
