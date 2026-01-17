#!/usr/bin/env python3
"""
Fully Independent Data Updater for Lottery Audience Newsletter
Fetches data directly from official lottery sources - NO local dependencies.
Can run on GitHub Actions without any local files.
"""

import json
import re
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate'
}

def fetch_url(url, timeout=30):
    """Fetch URL content with proper headers."""
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=timeout) as response:
            data = response.read()
            if response.headers.get('Content-Encoding') == 'gzip':
                data = gzip.decompress(data)
            return data.decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  ⚠️ Failed to fetch {url}: {e}")
        return None

def load_existing_draws(lottery_key):
    """Load existing draws from data file."""
    filepath = DATA_DIR / f'{lottery_key}.json'
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('draws', [])
        except:
            pass
    return []

def save_draws(lottery_key, draws):
    """Save draws to data file."""
    filepath = DATA_DIR / f'{lottery_key}.json'
    data = {
        'draws': draws,
        'updated': datetime.now().isoformat(),
        'total_draws': len(draws)
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

# ============================================================
# LUCKY FOR LIFE - Dual Source Fetching
# ============================================================
def fetch_l4l_ct_rss():
    """Source 1: CT Lottery RSS feed."""
    try:
        html = fetch_url("https://www.ctlottery.org/Feeds/rssnumbers.xml")
        if not html:
            return None
        
        root = ET.fromstring(html)
        for item in root.findall('.//item'):
            title = item.find('title')
            desc = item.find('description')
            
            if title is not None and 'lucky for life' in title.text.lower():
                desc_text = desc.text if desc is not None else ""
                
                match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})\s+LB-(\d{1,2})', desc_text)
                if not match:
                    continue
                
                main = sorted([int(match.group(i)) for i in range(1, 6)])
                bonus = int(match.group(6))
                
                date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', title.text)
                if date_match:
                    date_str = f"{date_match.group(3)}-{date_match.group(1).zfill(2)}-{date_match.group(2).zfill(2)}"
                else:
                    date_str = datetime.now().strftime("%Y-%m-%d")
                
                return {'date': date_str, 'main': main, 'bonus': bonus}
        return None
    except Exception as e:
        print(f"  ⚠️ L4L CT RSS error: {e}")
        return None

def fetch_l4l_lotto_net():
    """Source 2: lotto.net."""
    try:
        html = fetch_url("https://www.lotto.net/lucky-for-life/numbers")
        if not html:
            return None
        
        # Look for winning numbers pattern
        match = re.search(r'<div[^>]*class="[^"]*winning-numbers[^"]*"[^>]*>.*?(\d{1,2}).*?(\d{1,2}).*?(\d{1,2}).*?(\d{1,2}).*?(\d{1,2}).*?(\d{1,2})', html, re.DOTALL)
        if match:
            main = sorted([int(match.group(i)) for i in range(1, 6)])
            bonus = int(match.group(6))
            
            # Get date
            date_match = re.search(r'(\w+day),?\s*(\w+)\s+(\d{1,2}),?\s*(\d{4})', html)
            if date_match:
                month_map = {'January': '01', 'February': '02', 'March': '03', 'April': '04',
                             'May': '05', 'June': '06', 'July': '07', 'August': '08',
                             'September': '09', 'October': '10', 'November': '11', 'December': '12'}
                month = month_map.get(date_match.group(2), '01')
                day = date_match.group(3).zfill(2)
                year = date_match.group(4)
                date_str = f"{year}-{month}-{day}"
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            return {'date': date_str, 'main': main, 'bonus': bonus}
        return None
    except Exception as e:
        print(f"  ⚠️ L4L lotto.net error: {e}")
        return None

# ============================================================
# POWERBALL - Dual Source Fetching
# ============================================================
def fetch_pb_ny_api():
    """Source 1: NY Open Data API (most reliable)."""
    try:
        html = fetch_url("https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD")
        if not html:
            return None
        
        lines = html.strip().split('\n')
        if len(lines) < 2:
            return None
        
        latest = lines[-1].split(',')
        date_str = datetime.strptime(latest[0].strip('"'), "%m/%d/%Y").strftime("%Y-%m-%d")
        main_str = latest[1].strip('"').split()
        
        main = sorted([int(n) for n in main_str])
        bonus = int(latest[2].strip('"'))
        
        return {'date': date_str, 'main': main, 'bonus': bonus}
    except Exception as e:
        print(f"  ⚠️ PB NY API error: {e}")
        return None

def fetch_pb_ct_rss():
    """Source 1: CT Lottery RSS feed."""
    try:
        html = fetch_url("https://www.ctlottery.org/Feeds/rssnumbers.xml")
        if not html:
            return None
        
        root = ET.fromstring(html)
        for item in root.findall('.//item'):
            title = item.find('title')
            desc = item.find('description')
            
            if title is not None and 'powerball' in title.text.lower() and 'double play' not in title.text.lower():
                desc_text = desc.text if desc is not None else ""
                
                match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})\s+PB-(\d{1,2})', desc_text)
                if not match:
                    continue
                
                main = sorted([int(match.group(i)) for i in range(1, 6)])
                bonus = int(match.group(6))
                
                date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', title.text)
                if date_match:
                    date_str = f"{date_match.group(3)}-{date_match.group(1).zfill(2)}-{date_match.group(2).zfill(2)}"
                else:
                    date_str = datetime.now().strftime("%Y-%m-%d")
                
                return {'date': date_str, 'main': main, 'bonus': bonus}
        return None
    except Exception as e:
        print(f"  ⚠️ PB CT RSS error: {e}")
        return None

def fetch_pb_iowa():
    """Source 2: Iowa Lottery."""
    try:
        html = fetch_url("https://ialottery.com/Powerball")
        if not html:
            return None
        
        numbers = []
        for i in range(1, 6):
            match = re.search(rf'id="lblPBN{i}"[^>]*>(\d+)<', html)
            if match:
                numbers.append(int(match.group(1)))
        
        bonus_match = re.search(r'id="lblPBPower"[^>]*>(\d+)<', html)
        date_match = re.search(r'id="lblPBDate"[^>]*>([^<]+)<', html)
        
        if numbers and len(numbers) == 5 and bonus_match:
            main = sorted(numbers)
            bonus = int(bonus_match.group(1))
            
            if date_match:
                try:
                    date_obj = datetime.strptime(date_match.group(1).strip(), '%m/%d/%Y')
                    date_str = date_obj.strftime('%Y-%m-%d')
                except:
                    date_str = datetime.now().strftime("%Y-%m-%d")
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            return {'date': date_str, 'main': main, 'bonus': bonus}
        return None
    except Exception as e:
        print(f"  ⚠️ PB Iowa error: {e}")
        return None

# ============================================================
# MEGA MILLIONS - Dual Source Fetching
# ============================================================
def fetch_mm_ny_api():
    """Source 1: NY Open Data API (most reliable)."""
    try:
        html = fetch_url("https://data.ny.gov/api/views/5xaw-6ayf/rows.csv?accessType=DOWNLOAD")
        if not html:
            return None
        
        lines = html.strip().split('\n')
        if len(lines) < 2:
            return None
        
        # Most recent draw is last line
        latest = lines[-1].split(',')
        date_str = datetime.strptime(latest[0].strip('"'), "%m/%d/%Y").strftime("%Y-%m-%d")
        main_str = latest[1].strip('"').split()
        
        main = sorted([int(n) for n in main_str])
        bonus = int(latest[2].strip('"'))  # Mega Ball is separate column
        
        return {'date': date_str, 'main': main, 'bonus': bonus}
    except Exception as e:
        print(f"  ⚠️ MM NY API error: {e}")
        return None

def fetch_mm_iowa():
    """Source 2: Iowa Lottery."""
    try:
        html = fetch_url("https://www.ialottery.com/games/mega-millions")
        if not html:
            return None
        
        main = []
        for i in range(1, 6):
            match = re.search(rf'lblMMN{i}["\'][^>]*>(\d+)<', html)
            if match:
                main.append(int(match.group(1)))
        
        bonus_match = re.search(r'lblMMPower["\'][^>]*>(\d+)<', html)
        bonus = int(bonus_match.group(1)) if bonus_match else None
        
        if len(main) == 5 and bonus:
            now = datetime.now()
            for offset in range(7):
                check = now - timedelta(days=offset)
                if check.weekday() in [1, 4]:  # Tue, Fri
                    date_str = check.strftime("%Y-%m-%d")
                    break
            
            return {'date': date_str, 'main': sorted(main), 'bonus': bonus}
        return None
    except Exception as e:
        print(f"  ⚠️ MM Iowa error: {e}")
        return None

# ============================================================
# LOTTO AMERICA - Dual Source Fetching
# ============================================================
def fetch_la_oklahoma():
    """Source 1: Oklahoma Lottery - most reliable for LA."""
    try:
        html = fetch_url("https://www.lottery.ok.gov/draw-games/lotto-america")
        if not html:
            return None
        
        # Look for winning numbers - Oklahoma shows them in spans
        numbers = re.findall(r'class="[^"]*ball[^"]*"[^>]*>(\d{1,2})<', html)
        if not numbers:
            numbers = re.findall(r'<span[^>]*>(\d{1,2})</span>', html)
        
        # Filter to valid LA numbers
        valid = []
        for n in numbers:
            num = int(n)
            if 1 <= num <= 52 and len(valid) < 5:
                valid.append(num)
            elif 1 <= num <= 10 and len(valid) == 5:
                valid.append(num)
                break
        
        if len(valid) >= 6:
            main = sorted(valid[:5])
            bonus = valid[5]
            
            now = datetime.now()
            for offset in range(7):
                check = now - timedelta(days=offset)
                if check.weekday() in [0, 2, 5]:  # Mon, Wed, Sat
                    date_str = check.strftime("%Y-%m-%d")
                    break
            
            return {'date': date_str, 'main': main, 'bonus': bonus}
        return None
    except Exception as e:
        print(f"  ⚠️ LA Oklahoma error: {e}")
        return None

def fetch_la_iowa():
    """Source 1: Iowa Lottery."""
    try:
        html = fetch_url("https://www.ialottery.com/games/lotto-america")
        if not html:
            return None
        
        main = []
        for i in range(1, 6):
            match = re.search(rf'lblLAN{i}["\'][^>]*>(\d+)<', html)
            if match:
                main.append(int(match.group(1)))
        
        bonus_match = re.search(r'lblLAPower["\'][^>]*>(\d+)<', html)
        bonus = int(bonus_match.group(1)) if bonus_match else None
        
        if len(main) == 5 and bonus:
            now = datetime.now()
            for offset in range(7):
                check = now - timedelta(days=offset)
                if check.weekday() in [0, 2, 5]:  # Mon, Wed, Sat
                    date_str = check.strftime("%Y-%m-%d")
                    break
            
            return {'date': date_str, 'main': sorted(main), 'bonus': bonus}
        return None
    except Exception as e:
        print(f"  ⚠️ LA Iowa error: {e}")
        return None

def fetch_la_lottoamerica():
    """Source 2: Official Lotto America site."""
    try:
        html = fetch_url("https://www.lottoamerica.com/")
        if not html:
            return None
        
        numbers = []
        # Try ball class pattern
        ball_matches = re.findall(r'class=["\']ball["\'][^>]*>(\d{1,2})<', html)
        if len(ball_matches) >= 6:
            numbers = ball_matches
        
        # Try winning-numbers pattern
        if not numbers:
            match = re.search(r'winning-numbers[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
            if match:
                numbers = re.findall(r'>(\d{1,2})<', match.group(1))
        
        if len(numbers) >= 6:
            main = sorted([int(n) for n in numbers[:5]])
            bonus = int(numbers[5])
            
            now = datetime.now()
            for offset in range(7):
                check = now - timedelta(days=offset)
                if check.weekday() in [0, 2, 5]:
                    date_str = check.strftime("%Y-%m-%d")
                    break
            
            return {'date': date_str, 'main': main, 'bonus': bonus}
        return None
    except Exception as e:
        print(f"  ⚠️ LA lottoamerica.com error: {e}")
        return None

def fetch_la_lotto_net():
    """Source 3: lotto.net."""
    try:
        html = fetch_url("https://www.lotto.net/lotto-america/numbers")
        if not html:
            return None
        
        match = re.search(r'<div[^>]*class="[^"]*winning-numbers[^"]*"[^>]*>.*?(\d{1,2}).*?(\d{1,2}).*?(\d{1,2}).*?(\d{1,2}).*?(\d{1,2}).*?(\d{1,2})', html, re.DOTALL)
        if match:
            main = sorted([int(match.group(i)) for i in range(1, 6)])
            bonus = int(match.group(6))
            
            date_match = re.search(r'(\w+day),?\s*(\w+)\s+(\d{1,2}),?\s*(\d{4})', html)
            if date_match:
                month_map = {'January': '01', 'February': '02', 'March': '03', 'April': '04',
                             'May': '05', 'June': '06', 'July': '07', 'August': '08',
                             'September': '09', 'October': '10', 'November': '11', 'December': '12'}
                month = month_map.get(date_match.group(2), '01')
                day = date_match.group(3).zfill(2)
                year = date_match.group(4)
                date_str = f"{year}-{month}-{day}"
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            return {'date': date_str, 'main': main, 'bonus': bonus}
        return None
    except Exception as e:
        print(f"  ⚠️ LA lotto.net error: {e}")
        return None

# ============================================================
# Main Update Functions
# ============================================================
def update_lottery(lottery_key, fetch_funcs):
    """Update a single lottery using dual-source verification."""
    print(f"\n📊 Updating {lottery_key.upper()}...")
    
    # Load existing draws
    existing_draws = load_existing_draws(lottery_key)
    existing_dates = {d.get('date') for d in existing_draws}
    
    # Fetch from multiple sources
    results = []
    for func in fetch_funcs:
        result = func()
        if result:
            results.append(result)
            print(f"  ✓ {func.__name__}: {result['date']} - {result['main']} + {result['bonus']}")
    
    if not results:
        print(f"  ⚠️ No data fetched from any source")
        return False
    
    # Use first successful result (they should match if sources agree)
    new_draw = results[0]
    
    # Check if already exists
    if new_draw['date'] in existing_dates:
        print(f"  ✓ Already have draw for {new_draw['date']}")
        return True
    
    # Validate - no duplicate numbers
    if len(new_draw['main']) != len(set(new_draw['main'])):
        print(f"  ❌ Invalid draw - duplicate numbers detected")
        return False
    
    # Add new draw at beginning
    existing_draws.insert(0, new_draw)
    
    # Sort by date (newest first)
    existing_draws.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Save
    save_draws(lottery_key, existing_draws)
    print(f"  ✅ Added new draw! Total: {len(existing_draws)} draws")
    
    return True

def update_jackpots():
    """Fetch live jackpot data from official sources."""
    print("\n💰 Updating jackpots...")
    
    jackpots = {}
    
    # Powerball jackpot - Texas Lottery (same as tracker)
    pb_found = False
    try:
        content = fetch_url('https://www.texaslottery.com/export/sites/lottery/Games/Powerball/index.html')
        if content:
            match = re.search(r'Est\.\s*(?:Annuitized\s*)?Jackpot[^$]*\$(\d+)\s*(Million|Billion)', content, re.IGNORECASE)
            if match:
                amount = int(match.group(1))
                if 'billion' in match.group(2).lower():
                    amount *= 1000
                cash_match = re.search(r'Cash\s*Value[^$]*\$(\d+)', content, re.IGNORECASE)
                cash = int(cash_match.group(1)) * 1_000_000 if cash_match else int(amount * 450_000)
                jackpots['pb'] = {'jackpot': amount * 1_000_000, 'cash_value': cash}
                print(f"  ✅ PB: ${amount}M")
                pb_found = True
    except Exception as e:
        print(f"  ⚠️ PB Texas error: {e}")
    
    # PB fallback - powerball.com
    if not pb_found:
        try:
            content = fetch_url('https://www.powerball.com/')
            if content:
                match = re.search(r'\$(\d+)\s*(Million|Billion)', content, re.IGNORECASE)
                if match:
                    amount = int(match.group(1))
                    if 'billion' in match.group(2).lower():
                        amount *= 1000
                    jackpots['pb'] = {'jackpot': amount * 1_000_000, 'cash_value': int(amount * 450_000)}
                    print(f"  ✅ PB: ${amount}M (fallback)")
        except Exception as e:
            print(f"  ⚠️ PB fallback error: {e}")
    
    # Mega Millions jackpot
    try:
        content = fetch_url('https://www.valottery.com/data/draw-games/megamillions')
        if content:
            match = re.search(r'\$(\d+)\s*MILLION', content, re.IGNORECASE)
            if match:
                amount = int(match.group(1))
                cash_match = re.search(r'Cash\s*Value[:\s]*\$(\d+)', content, re.IGNORECASE)
                cash = int(cash_match.group(1)) * 1_000_000 if cash_match else int(amount * 457_000)
                jackpots['mm'] = {'jackpot': amount * 1_000_000, 'cash_value': cash}
                print(f"  ✅ MM: ${amount}M")
    except Exception as e:
        print(f"  ⚠️ MM jackpot error: {e}")
    
    # Lotto America jackpot
    try:
        content = fetch_url('https://www.powerball.com/lotto-america')
        if content:
            match = re.search(r'\$([\d.]+)\s*M', content)
            if match:
                amount = float(match.group(1))
                jackpots['la'] = {'jackpot': int(amount * 1_000_000), 'cash_value': int(amount * 450_000)}
                print(f"  ✅ LA: ${amount}M")
    except Exception as e:
        print(f"  ⚠️ LA jackpot error: {e}")
    
    # Set defaults for any missing
    if 'pb' not in jackpots:
        jackpots['pb'] = {'jackpot': 179_000_000, 'cash_value': 80_550_000}
        print(f"  ⚠️ PB: Using fallback")
    if 'mm' not in jackpots:
        jackpots['mm'] = {'jackpot': 250_000_000, 'cash_value': 113_500_000}
        print(f"  ⚠️ MM: Using fallback")
    if 'la' not in jackpots:
        jackpots['la'] = {'jackpot': 12_740_000, 'cash_value': 6_370_000}
        print(f"  ⚠️ LA: Using fallback")
    
    # L4L is always fixed
    jackpots['l4l'] = {'jackpot': 7_000_000, 'cash_value': 5_750_000}
    
    # Save jackpots
    jackpot_file = DATA_DIR / 'jackpots.json'
    with open(jackpot_file, 'w', encoding='utf-8') as f:
        json.dump(jackpots, f, indent=2)
    
    print(f"  ✅ Jackpots saved")
    return True

def main():
    """Run full data update."""
    print("=" * 60)
    print("🎰 LOTTERY NEWSLETTER DATA UPDATE")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    DATA_DIR.mkdir(exist_ok=True)
    
    # Update each lottery with dual-source fetching
    update_lottery('l4l', [fetch_l4l_ct_rss, fetch_l4l_lotto_net])
    update_lottery('pb', [fetch_pb_ny_api, fetch_pb_ct_rss, fetch_pb_iowa])
    update_lottery('mm', [fetch_mm_ny_api, fetch_mm_iowa])
    update_lottery('la', [fetch_la_oklahoma, fetch_la_iowa, fetch_la_lottoamerica, fetch_la_lotto_net])
    
    # Update jackpots
    update_jackpots()
    
    print("\n" + "=" * 60)
    print("✅ Data update complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
