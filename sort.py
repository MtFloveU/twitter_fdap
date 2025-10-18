import asyncio
import json
import os
import runpy
import sys
import configparser
import shutil
import datetime
from pathlib import Path

config = configparser.ConfigParser()
config.read(os.path.abspath('config.ini'))
TWITTER_ID = config.get('General', 'TWITTER_ID')
source_dir = "temp/data"
target_dir = os.path.join("data", TWITTER_ID)

async def split_files():
    await asyncio.to_thread(runpy.run_path, "sort/unique.py", run_name="__main__")
    sys.argv = ["sort/split.py", f"--target-dir={target_dir}"]
    await asyncio.to_thread(runpy.run_path, "sort/split.py", run_name="__main__")
    print("Success")

async def first_run():
    os.makedirs(f"{target_dir}/removed", exist_ok=True)
    for filename in os.listdir(source_dir):
         if filename.endswith('.json'):
             source_file = os.path.join(source_dir, filename)
             target_file = os.path.join(target_dir, filename)
             os.rename(source_file, target_file)
    print("An initial database has been created. You can run it again if your followers list changes in the future.")
    exit(0)

async def report():
    Path.touch(Path("diff.md"))
    with open("./diff.md", "w", encoding='utf-8') as f:
        f.write(f"🕒Time: `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}`")
    with open("./diff.md", "a", encoding='utf-8') as f:
        f.write(f"\n📊Total followers: `{len(json.load(open('./temp/twitter-Followers.json', encoding='utf-8')))}`, following: `{len(json.load(open('./temp/twitter-Following.json', encoding='utf-8')))}`\n")
    mutual = os.path.join(source_dir, 'mutual_unfollow.txt')
    single_unfollower = os.path.join(source_dir, 'single-unfollower.txt')
    single_unfollowing = os.path.join(source_dir, 'single-unfollowing.txt')

    if os.path.getsize(mutual) > 0:
        with open('diff.md', 'a', encoding='utf-8') as diff, open(mutual, encoding='utf-8') as f:
            diff.write('*Mutual Unfollow or Removal:*\n')
            for id in f:
                id = id.strip()
                src = os.path.join(target_dir, f'{id}.json')
                if os.path.isfile(src):
                    data = json.load(open(src, encoding='utf-8'))
                    name = data['name'].replace('`', ''); sn = data['screen_name']
                    diff.write(f'`{name}` @`{sn}`\n')
                    shutil.move(src, os.path.join(target_dir, 'removed', os.path.basename(src)))
                    with open(os.path.join(target_dir, 'removed_list.txt'), 'a', encoding='utf-8') as rl:
                        rl.write(id + '\n')
            diff.write('\n')

    if os.path.getsize(single_unfollower) > 0:
        with open('diff.md', 'a', encoding='utf-8') as diff, open(single_unfollower, encoding='utf-8') as f:
            diff.write('*One-Way Unfollowers:*\n')
            for id in f:
                id = id.strip()
                src = os.path.join(target_dir, f'{id}.json')
                if os.path.isfile(src):
                    data = json.load(open(src, encoding='utf-8'))
                    name = data['name'].replace('`', ''); sn = data['screen_name']
                    diff.write(f'`{name}` @`{sn}`\n')
            diff.write('\n')

    if os.path.getsize(single_unfollowing) > 0:
        with open('diff.md', 'a', encoding='utf-8') as diff, open(single_unfollowing, encoding='utf-8') as f:
            diff.write('*One-Way Unfollowing:*\n')
            for id in f:
                id = id.strip()
                src = os.path.join(target_dir, f'{id}.json')
                if os.path.isfile(src):
                    data = json.load(open(src, encoding='utf-8'))
                    name = data['name'].replace('`', ''); sn = data['screen_name']
                    diff.write(f'`{name}` @`{sn}`\n')
            diff.write('\n')
    with open(os.path.join(source_dir, 'single-unfollower.txt'), 'r', encoding='utf-8') as single_unfollower_file:
        single_unfollower_ids = single_unfollower_file.readlines()

    mutual_unfollow_path = os.path.join(source_dir, 'mutual_unfollow.txt')
    if os.path.exists(mutual_unfollow_path):
        with open(mutual_unfollow_path, 'r', encoding='utf-8') as mutual_unfollow_file:
            mutual_ids = set(line.strip() for line in mutual_unfollow_file)

        updated_ids = []
        for id in single_unfollower_ids:
            id = id.strip()
            if id not in mutual_ids:
                updated_ids.append(id)

        updated_ids = sorted(set(updated_ids))
        with open(os.path.join(source_dir, 'single-unfollower.txt'), 'w', encoding='utf-8') as single_unfollower_file:
            single_unfollower_file.write('\n'.join(updated_ids) + '\n')
    removed_list_path = os.path.join(target_dir, 'removed_list.txt')
    if os.path.exists(removed_list_path):
        with open(removed_list_path, 'r', encoding='utf-8') as removed_list_file:
            removed_list = [line.strip() for line in removed_list_file]
    else:
        Path(removed_list_path).touch()
        removed_list = []

    returners_path = os.path.join(source_dir, 'returners.txt')
    with open(returners_path, 'w', encoding='utf-8') as returners_file:
        for source_file in Path(source_dir).glob('*.json'):
            with open(source_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                id = data.get('id')

            if id in removed_list:
                target_file = os.path.join(target_dir, 'removed', f'{id}.json')

                if os.path.exists(target_file):
                    name = data.get('name', '').replace('`', '')
                    screen_name = data.get('screen_name', '')
                    returners_file.write(f'`{name}` @`{screen_name}`\n')
                    os.remove(target_file)
                    removed_list.remove(id)

    with open(removed_list_path, 'w', encoding='utf-8') as removed_list_file:
        removed_list_file.write('\n'.join(removed_list) + '\n')

    single_unfollower_return_path = os.path.join(source_dir, 'single-unfollower-return.txt')
    single_unfollower_returner_name_path = os.path.join(source_dir, 'single-unfollower-returner-name.txt')
    if os.path.exists(single_unfollower_return_path) and os.path.getsize(single_unfollower_return_path) > 0:
        with open(single_unfollower_return_path, 'r', encoding='utf-8') as f, open(single_unfollower_returner_name_path, 'w',encoding='utf-8') as returner_name_file:
            for id in f:
                id = id.strip()
                source_file = os.path.join(source_dir, f'{id}.json')

                if os.path.exists(source_file):
                    with open(source_file, 'r', encoding='utf-8') as sf:
                        data = json.load(sf)
                        name = data.get('name', '').replace('`', '')
                        screen_name = data.get('screen_name', '')
                        returner_name_file.write(f'`{name}` @`{screen_name}`\n')

    diff_path = './diff.md'
    if (os.path.exists(returners_path) and os.path.getsize(returners_path) > 0) or \
       (os.path.exists(single_unfollower_returner_name_path) and os.path.getsize(single_unfollower_returner_name_path) > 0):
        with open(diff_path, 'a', encoding='utf-8') as diff_file:
            diff_file.write('*Returning Follows:*\n')

            if os.path.exists(returners_path) and os.path.getsize(returners_path) > 0:
                with open(returners_path, 'r', encoding='utf-8') as returners_file:
                    diff_file.write(returners_file.read())

            if os.path.exists(single_unfollower_returner_name_path) and os.path.getsize(single_unfollower_returner_name_path) > 0:
                with open(single_unfollower_returner_name_path, 'r', encoding='utf-8') as returner_name_file:
                    diff_file.write(returner_name_file.read())
    
async def update_data():
    removed_list_path = os.path.join(target_dir, 'removed_list.txt')
    if os.path.exists(removed_list_path):
        with open(removed_list_path, 'r', encoding='utf-8') as removed_list_file:
            removed_list = [line.strip() for line in removed_list_file if line.strip()]
    else:
        removed_list = []

    with open(removed_list_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(removed_list) + '\n')

    with open(removed_list_path, 'r', encoding='utf-8') as f:
        unique_removed_list = sorted(set(line.strip() for line in f if line.strip()))

    with open(removed_list_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(unique_removed_list) + '\n')

    single_unfollower_path = os.path.join(source_dir, 'single-unfollower.txt')
    single_unfollower_return_path = os.path.join(source_dir, 'single-unfollower-return.txt')

    if os.path.exists(single_unfollower_path):
        with open(single_unfollower_path, 'r', encoding='utf-8') as f:
            single_unfollower_ids = [line.strip() for line in f if line.strip()]

        if os.path.exists(single_unfollower_return_path):
            with open(single_unfollower_return_path, 'r', encoding='utf-8') as f:
                return_ids = set(line.strip() for line in f if line.strip())

            single_unfollower_ids = [id for id in single_unfollower_ids if id not in return_ids]

        single_unfollower_ids = sorted(set(single_unfollower_ids))
        with open(single_unfollower_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(single_unfollower_ids) + '\n')

    source_single_unfollower_path = os.path.join(source_dir, 'single-unfollower.txt')
    if os.path.exists(source_single_unfollower_path):
        with open(source_single_unfollower_path, 'r', encoding='utf-8') as f:
            source_ids = [line.strip() for line in f if line.strip()]

        with open(single_unfollower_path, 'r', encoding='utf-8') as f:
            target_ids = [line.strip() for line in f if line.strip()]

        combined_ids = sorted(set(source_ids + target_ids))
        with open(single_unfollower_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(combined_ids) + '\n')
    sys.argv = ["sort/upd.py", f"--target-dir={target_dir}"]
    await asyncio.to_thread(runpy.run_path, "sort/upd.py", run_name="__main__")
    # os.rename("diff.md", f"{target_dir}/diff.md")
    os.replace("diff.md", f"{target_dir}/diff.md")

async def github_push():
    parent_dir = os.path.dirname(target_dir)
    os.chdir(parent_dir)
    await asyncio.to_thread(os.system, "git add --all")
    await asyncio.to_thread(os.system, f'git commit -m "{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}" > /dev/null')
    if config.getboolean("Git", "REMOTE") == True:
        print("\nPushing to remote repository...", end="", flush=True)
        await asyncio.to_thread(os.system, "git push --force")
    os.chdir("..")

async def telegram_push():
    print("Sending report to Telegram...", end="", flush=True)
    await asyncio.to_thread(runpy.run_path, "tgbot.py", run_name="__main__")
        

async def main():
    print("Starting file procession...")
    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(target_dir, exist_ok=True)
    await asyncio.sleep(0.5)
    print("Splitting files...", end="", flush=True)
    await split_files()
    if config.getboolean("General", "NOT_FIRST_RUN") == False and config.getboolean("General", "DATABASE_EXIST") == False:
        await first_run()
    print("Finding mutual unfollowers...", end="", flush=True)
    sys.argv = ["sort/step1.py", f"--target-dir={target_dir}"]
    await asyncio.to_thread(runpy.run_path, "sort/step1.py", run_name="__main__")
    print("Success")
    print("Finding one-way unfollowers...", end="", flush=True)
    sys.argv = ["sort/step2.py", f"--target-dir={target_dir}"]
    await asyncio.to_thread(runpy.run_path, "sort/step2.py", run_name="__main__")
    print("Success")
    print("Finding one-way unfollowing...", end="", flush=True)
    sys.argv = ["sort/step3.py", f"--target-dir={target_dir}"]
    await asyncio.to_thread(runpy.run_path, "sort/step3.py", run_name="__main__")
    print("Success")
    print("Finding returned follows...", end="", flush=True)
    sys.argv = ["sort/step4.py", f"--target-dir={target_dir}"]
    await asyncio.to_thread(runpy.run_path, "sort/step4.py", run_name="__main__")
    print("Success")
    print("Generating report...", end="", flush=True)
    await report()
    print("Success")
    print("Updating data...", end="", flush=True)
    await update_data()
    print("Success")
    print("Committing changes...", end="", flush=True)
    await github_push()
    print("Success")
    if config.has_section("Telegram") and \
       config.has_option("Telegram", "PUSH") and \
       config.has_option("Telegram", "API_KEY") and \
       config.has_option("Telegram", "USER_ID") and \
       config.getboolean("Telegram", "PUSH") and \
       config.get("Telegram", "API_KEY") != "" and \
       config.get("Telegram", "USER_ID") != "":
        await telegram_push()
    print("All done! You can check the report in diff.md.")
    exit(0)

if __name__ == "__main__":
    asyncio.run(main())
