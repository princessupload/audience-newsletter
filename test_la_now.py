"""Test LA fetch right now."""
import urllib.request
import re

url = "https://www.lotteryusa.com/lotto-america/"
headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request(url, headers=headers)

with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Find c-ball numbers
balls = re.findall(r'c-ball[^>]*>(\d+)<', html)
print(f"Found {len(balls)} balls total")

if len(balls) >= 6:
    main = sorted([int(balls[i]) for i in range(5)])
    bonus = int(balls[5])
    print(f"\nLatest LA Draw: {main} + Star Ball {bonus}")
else:
    print("c-ball pattern not found, trying alternative...")
    # Try alternative pattern
    balls2 = re.findall(r'class="[^"]*ball[^"]*"[^>]*>(\d+)<', html)
    print(f"Alternative found: {balls2[:10]}")
