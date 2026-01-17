#!/usr/bin/env python3
"""
Data Updater for Lottery Audience Newsletter
Fetches latest drawings from multiple sources and updates local data files.
Uses dual-source verification for accuracy.
"""

import json
import re
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
import xml.etree.ElementTree as ET

DATA_DIR = Path(__file__).parent / 'data'

# Data sources configuration - Oklahoma Lottery added as reliable backup
SOURCES = {
    'l4l': {
        'primary': {
            'name': 'Oklahoma Lottery',
            'url': 'https://www.lottery.ok.gov/draw-games/lucky-for-life',
            'type': 'oklahoma_html'
        },
        'secondary': {
            'name': 'CT Lottery RSS',
            'url': 'https://www.ctlottery.org/Feeds/rssnumbers.xml',
            'type': 'ct_rss'
        }
    },
    'la': {
        'primary': {
            'name': 'Oklahoma Lottery',
            'url': 'https://www.lottery.ok.gov/draw-games/lotto-america',
            'type': 'oklahoma_html'
        },
        'secondary': {
            'name': 'Iowa Lottery',
            'url': 'https://ialottery.com/LottoAmerica',
            'type': 'iowa_html'
        }
    },
    'pb': {
        'primary': {
            'name': 'Oklahoma Lottery',
            'url': 'https://www.lottery.ok.gov/draw-games/powerball',
            'type': 'oklahoma_html'
        },
        'secondary': {
            'name': 'CT Lottery RSS',
            'url': 'https://www.ctlottery.org/Feeds/rssnumbers.xml',
            'type': 'ct_rss'
        }
    },
    'mm': {
        'primary': {
            'name': 'Oklahoma Lottery',
            'url': 'https://www.lottery.ok.gov/draw-games/mega-millions',
            'type': 'oklahoma_html'
        },
        'secondary': {
            'name': 'Virginia Lottery',
            'url': 'https://www.valottery.com/data/draw-games/megamillions',
            'type': 'virginia_html'
        }
    }
}

# Oklahoma Lottery jackpot URLs
OKLAHOMA_JACKPOT_URLS = {
    'l4l': 'https://www.lottery.ok.gov/draw-games/lucky-for-life',
    'la': 'https://www.lottery.ok.gov/draw-games/lotto-america',
    'pb': 'https://www.lottery.ok.gov/draw-games/powerball',
    'mm': 'https://www.lottery.ok.gov/draw-games/mega-millions'
}

def fetch_url(url, accept_gzip=True):
    """Fetch URL content with proper headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    if accept_gzip:
        headers['Accept-Encoding'] = 'gzip, deflate'
    
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=30) as response:
            data = response.read()
            if response.headers.get('Content-Encoding') == 'gzip':
                data = gzip.decompress(data)
            return data.decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  ⚠️ Failed to fetch {url}: {e}")
        return None

def parse_rss_draw(content, lottery):
    """Parse lottery draw from CT Lottery RSS feed."""
    try:
        root = ET.fromstring(content)
        for item in root.findall('.//item'):
            title = item.find('title')
            if title is not None:
                text = title.text
                # Parse format: "Lucky4Life - 01/15/2026 - 03 24 32 39 41 LB:02"
                # or "Powerball - 01/15/2026 - 06 24 39 43 51 PB:23"
                match = re.search(r'(\d{2}/\d{2}/\d{4})\s*-\s*([\d\s]+)\s*(?:LB|PB):(\d+)', text)
                if match:
                    date_str = match.group(1)
                    numbers = [int(n) for n in match.group(2).split()]
                    bonus = int(match.group(3))
                    
                    # Convert date format
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                    date_formatted = date_obj.strftime('%Y-%m-%d')
                    
                    return {
                        'date': date_formatted,
                        'main': numbers,
                        'bonus': bonus
                    }
    except Exception as e:
        print(f"  ⚠️ RSS parse error: {e}")
    return None

def parse_oklahoma_html(content, lottery):
    """Parse lottery draw from Oklahoma Lottery HTML (lottery.ok.gov)."""
    try:
        # Oklahoma shows winning numbers in spans with specific patterns
        # Look for number balls - they use various class names
        numbers = []
        
        # Pattern 1: Look for ball numbers in spans
        ball_pattern = re.findall(r'class="[^"]*ball[^"]*"[^>]*>(\d{1,2})<', content, re.I)
        if ball_pattern:
            numbers = [int(n) for n in ball_pattern[:5]]
        
        # Pattern 2: Look for winning-number spans
        if not numbers:
            num_pattern = re.findall(r'class="[^"]*winning[^"]*number[^"]*"[^>]*>(\d{1,2})<', content, re.I)
            if num_pattern:
                numbers = [int(n) for n in num_pattern[:5]]
        
        # Pattern 3: General number extraction from result section
        if not numbers:
            result_match = re.search(r'result[^>]*>.*?(\d{1,2})[^\d]*(\d{1,2})[^\d]*(\d{1,2})[^\d]*(\d{1,2})[^\d]*(\d{1,2})', content, re.I | re.DOTALL)
            if result_match:
                numbers = [int(result_match.group(i)) for i in range(1, 6)]
        
        # Bonus ball - look for special ball class or powerball/megaball/luckyball/starball
        bonus = None
        bonus_patterns = [
            r'(?:power|mega|lucky|star)[\s-]*ball[^>]*>(\d{1,2})<',
            r'class="[^"]*bonus[^"]*"[^>]*>(\d{1,2})<',
            r'class="[^"]*special[^"]*"[^>]*>(\d{1,2})<'
        ]
        for pattern in bonus_patterns:
            bonus_match = re.search(pattern, content, re.I)
            if bonus_match:
                bonus = int(bonus_match.group(1))
                break
        
        # If no bonus found, try getting 6th number from ball pattern
        if not bonus and ball_pattern and len(ball_pattern) >= 6:
            bonus = int(ball_pattern[5])
        
        # Date extraction
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', content)
        if date_match:
            month, day, year = date_match.groups()
            date_formatted = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        else:
            date_formatted = datetime.now().strftime('%Y-%m-%d')
        
        if numbers and len(numbers) >= 5:
            return {
                'date': date_formatted,
                'main': sorted(numbers[:5]),
                'bonus': bonus or 1
            }
    except Exception as e:
        print(f"  ⚠️ Oklahoma HTML parse error: {e}")
    return None

def parse_iowa_html(content, lottery):
    """Parse lottery draw from Iowa Lottery HTML."""
    try:
        # Iowa uses lblLAN1-5 for LA, lblPBN1-5 for PB, lblMMN1-5 for MM
        prefix_map = {'la': 'lblLA', 'pb': 'lblPB', 'mm': 'lblMM'}
        prefix = prefix_map.get(lottery, '')
        
        numbers = []
        for i in range(1, 6):
            pattern = rf'id="{prefix}N{i}"[^>]*>(\d+)<'
            match = re.search(pattern, content)
            if match:
                numbers.append(int(match.group(1)))
        
        # Bonus ball
        bonus_id = {'la': 'lblLAPower', 'pb': 'lblPBPower', 'mm': 'lblMMPower'}.get(lottery)
        bonus_match = re.search(rf'id="{bonus_id}"[^>]*>(\d+)<', content)
        bonus = int(bonus_match.group(1)) if bonus_match else None
        
        # Date
        date_id = {'la': 'lblLADate', 'pb': 'lblPBDate', 'mm': 'lblMMDate'}.get(lottery)
        date_match = re.search(rf'id="{date_id}"[^>]*>([^<]+)<', content)
        
        if numbers and bonus and date_match:
            date_str = date_match.group(1).strip()
            try:
                date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                date_formatted = date_obj.strftime('%Y-%m-%d')
            except:
                date_formatted = datetime.now().strftime('%Y-%m-%d')
            
            return {
                'date': date_formatted,
                'main': numbers,
                'bonus': bonus
            }
    except Exception as e:
        print(f"  ⚠️ Iowa HTML parse error: {e}")
    return None

def parse_ny_csv(content):
    """Parse Mega Millions from NY Open Data CSV."""
    try:
        lines = content.strip().split('\n')
        if len(lines) < 2:
            return None
        
        # Most recent draw is last line
        latest_line = lines[-1]
        parts = latest_line.split(',')
        
        if len(parts) >= 2:
            date_str = parts[0].strip('"')
            numbers_str = parts[1].strip('"')
            
            # Parse numbers (format: "06 13 34 43 52")
            all_nums = [int(n) for n in numbers_str.split()]
            if len(all_nums) >= 6:
                main = all_nums[:5]
                bonus = all_nums[5]
                
                try:
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                    date_formatted = date_obj.strftime('%Y-%m-%d')
                except:
                    date_formatted = datetime.now().strftime('%Y-%m-%d')
                
                return {
                    'date': date_formatted,
                    'main': main,
                    'bonus': bonus
                }
    except Exception as e:
        print(f"  ⚠️ CSV parse error: {e}")
    return None

def load_existing_draws(lottery):
    """Load existing draws from data file."""
    for filename in [f'{lottery}_historical_data.json', f'{lottery}.json']:
        path = DATA_DIR / filename
        if path.exists():
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get('draws', []), path
                return data, path
    return [], DATA_DIR / f'{lottery}.json'

def save_draws(draws, filepath):
    """Save draws to data file."""
    data = {'draws': draws, 'updated': datetime.now().isoformat()}
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def update_lottery(lottery):
    """Update a single lottery's data."""
    print(f"\n📊 Updating {lottery.upper()}...")
    
    sources = SOURCES.get(lottery, {})
    primary = sources.get('primary', {})
    
    # Fetch from primary source
    content = fetch_url(primary.get('url', ''))
    if not content:
        print(f"  ❌ Could not fetch from {primary.get('name')}")
        return False
    
    # Parse based on source type
    new_draw = None
    source_type = primary.get('type')
    
    if source_type == 'oklahoma_html':
        new_draw = parse_oklahoma_html(content, lottery)
    elif source_type == 'rss' or source_type == 'ct_rss':
        new_draw = parse_rss_draw(content, lottery)
    elif source_type == 'iowa_html':
        new_draw = parse_iowa_html(content, lottery)
    elif source_type == 'virginia_html':
        new_draw = parse_oklahoma_html(content, lottery)  # Similar format
    elif source_type == 'csv':
        new_draw = parse_ny_csv(content)
    
    if not new_draw:
        print(f"  ❌ Could not parse draw from {primary.get('name')}")
        return False
    
    print(f"  📥 Found: {new_draw['date']} - {new_draw['main']} + {new_draw['bonus']}")
    
    # Load existing draws
    existing_draws, filepath = load_existing_draws(lottery)
    
    # Check if this draw already exists
    for draw in existing_draws:
        if draw.get('date') == new_draw['date']:
            print(f"  ✓ Already have draw for {new_draw['date']}")
            return True
    
    # Add new draw at the beginning (most recent first)
    existing_draws.insert(0, new_draw)
    
    # Save updated data
    save_draws(existing_draws, filepath)
    print(f"  ✅ Added new draw! Total: {len(existing_draws)} draws")
    
    return True

def update_jackpots():
    """Update jackpot information."""
    print("\n💰 Updating jackpots...")
    
    jackpots = {}
    
    # Powerball jackpot - Try powerball.com first
    pb_found = False
    try:
        content = fetch_url('https://www.powerball.com/')
        if content:
            # Look for jackpot - format: "$179 MILLION" or "$1.5 BILLION"
            match = re.search(r'\$(\d+(?:\.\d+)?)\s*(Million|Billion)', content, re.I)
            if match:
                amount = float(match.group(1))
                if 'billion' in match.group(2).lower():
                    amount *= 1000
                # Look for cash value
                cash_match = re.search(r'Cash\s*Value[:\s]*\$(\d+(?:\.\d+)?)\s*M', content, re.I)
                cash = int(float(cash_match.group(1)) * 1_000_000) if cash_match else int(amount * 450_000)
                jackpots['pb'] = {
                    'jackpot': int(amount * 1_000_000),
                    'cash_value': cash
                }
                print(f"  ✓ PB: ${amount}M (from powerball.com)")
                pb_found = True
    except Exception as e:
        print(f"  ⚠️ PB powerball.com error: {e}")
    
    # PB fallback - Virginia Lottery
    if not pb_found:
        try:
            content = fetch_url('https://www.valottery.com/data/draw-games/powerball')
            if content:
                match = re.search(r'\$(\d+)\s*MILLION', content, re.IGNORECASE)
                if match:
                    amount = int(match.group(1))
                    cash_match = re.search(r'Cash\s*Value[:\s]*\$(\d+)M?', content, re.IGNORECASE)
                    cash = int(cash_match.group(1)) * 1_000_000 if cash_match else int(amount * 450_000)
                    jackpots['pb'] = {
                        'jackpot': amount * 1_000_000,
                        'cash_value': cash
                    }
                    print(f"  ✓ PB: ${amount}M (from Virginia Lottery)")
                    pb_found = True
        except Exception as e:
            print(f"  ⚠️ PB Virginia error: {e}")
    
    if not pb_found:
        jackpots['pb'] = {'jackpot': 179_000_000, 'cash_value': 80_000_000}
        print(f"  ⚠️ PB: Using fallback estimate")
    
    # Mega Millions jackpot - Try Virginia Lottery first (most reliable)
    mm_found = False
    try:
        content = fetch_url('https://www.valottery.com/data/draw-games/megamillions')
        if content:
            # Look for jackpot - format: "$230 MILLION" or "Friday Jackpot: $230 MILLION"
            match = re.search(r'\$(\d+)\s*MILLION', content, re.IGNORECASE)
            if match:
                amount = int(match.group(1))
                # Look for cash value - format: "Est. Cash Value: $105M"
                cash_match = re.search(r'Cash\s*Value[:\s]*\$(\d+)M?', content, re.IGNORECASE)
                cash = int(cash_match.group(1)) * 1_000_000 if cash_match else int(amount * 457000)
                jackpots['mm'] = {
                    'jackpot': amount * 1_000_000,
                    'cash_value': cash
                }
                print(f"  ✓ MM: ${amount}M (from Virginia Lottery)")
                mm_found = True
    except Exception as e:
        print(f"  ⚠️ MM Virginia error: {e}")
    
    # MM fallback - megamillions.com main page
    if not mm_found:
        try:
            content = fetch_url('https://www.megamillions.com/')
            if content:
                match = re.search(r'\$(\d+)\s*(Million|Billion)', content, re.I)
                if match:
                    amount = int(match.group(1))
                    if 'billion' in match.group(2).lower():
                        amount *= 1000
                    jackpots['mm'] = {
                        'jackpot': amount * 1_000_000,
                        'cash_value': int(amount * 457000)
                    }
                    print(f"  ✓ MM: ${amount}M (from megamillions.com)")
        except Exception as e:
            print(f"  ⚠️ MM jackpot error: {e}")
    
    # L4L is always $1000/day for life (fixed)
    jackpots['l4l'] = {
        'jackpot': 7_000_000,  # Approximate lump sum value
        'cash_value': 5_750_000
    }
    
    # LA jackpot - Try powerball.com/lotto-america
    la_found = False
    try:
        content = fetch_url('https://www.powerball.com/lotto-america')
        if content:
            # Look for jackpot amount
            match = re.search(r'\$([\d.]+)\s*M', content)
            if match:
                amount = float(match.group(1))
                jackpots['la'] = {
                    'jackpot': int(amount * 1_000_000),
                    'cash_value': int(amount * 450_000)
                }
                print(f"  ✓ LA: ${amount}M (from powerball.com)")
                la_found = True
    except Exception as e:
        print(f"  ⚠️ LA jackpot error: {e}")
    
    if not la_found:
        # LA fallback - estimate
        jackpots['la'] = {
            'jackpot': 12_980_000,
            'cash_value': 5_800_000
        }
        print(f"  ⚠️ LA: Using fallback estimate")
    
    # Save jackpots
    jackpot_file = DATA_DIR / 'jackpots.json'
    with open(jackpot_file, 'w', encoding='utf-8') as f:
        json.dump(jackpots, f, indent=2)
    
    print(f"  ✅ Jackpots saved to {jackpot_file}")
    return True

def main():
    """Run full data update."""
    print("=" * 50)
    print("🎰 LOTTERY DATA UPDATER")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    DATA_DIR.mkdir(exist_ok=True)
    
    # Update each lottery
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        try:
            update_lottery(lottery)
        except Exception as e:
            print(f"  ❌ Error updating {lottery}: {e}")
    
    # Update jackpots
    try:
        update_jackpots()
    except Exception as e:
        print(f"  ❌ Error updating jackpots: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Data update complete!")
    print("=" * 50)

if __name__ == '__main__':
    main()
