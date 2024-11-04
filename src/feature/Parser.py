import json
import subprocess

page_url = "netstalkers"

result = subprocess.run(
    ["snscrape", "--max-results", "1", "--jsonl-for-buggy-int-parser", "telegram-channel", page_url],
    capture_output=True,
    text=True
)

total = result.stdout

json_lines = total.strip().split('\n')

posts = [json.loads(line) for line in json_lines if line]

for post in posts:
    print(json.dumps(post, indent=4))
    if "url" in post:
        print(post["url"])
