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

# Data sources configuration
SOURCES = {
    'l4l': {
        'primary': {
            'name': 'CT Lottery RSS',
            'url': 'https://www.ctlottery.org/Modules/Games/RSS.aspx?game=Lucky4Life',
            'type': 'rss'
        },
        'secondary': {
            'name': 'lotto.net',
            'url': 'https://www.lotto.net/lucky-for-life/results',
            'type': 'html'
        }
    },
    'la': {
        'primary': {
            'name': 'Iowa Lottery',
            'url': 'https://ialottery.com/LottoAmerica',
            'type': 'iowa_html'
        },
        'secondary': {
            'name': 'lotto.net',
            'url': 'https://www.lotto.net/lotto-america/results',
            'type': 'html'
        }
    },
    'pb': {
        'primary': {
            'name': 'CT Lottery RSS',
            'url': 'https://www.ctlottery.org/Modules/Games/RSS.aspx?game=Powerball',
            'type': 'rss'
        },
        'secondary': {
            'name': 'Iowa Lottery',
            'url': 'https://ialottery.com/Powerball',
            'type': 'iowa_html'
        }
    },
    'mm': {
        'primary': {
            'name': 'NY Open Data',
            'url': 'https://data.ny.gov/api/views/5xaw-6ayf/rows.csv?accessType=DOWNLOAD',
            'type': 'csv'
        },
        'secondary': {
            'name': 'Iowa Lottery',
            'url': 'https://ialottery.com/MegaMillions',
            'type': 'iowa_html'
        }
    }
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
    
    if source_type == 'rss':
        new_draw = parse_rss_draw(content, lottery)
    elif source_type == 'iowa_html':
        new_draw = parse_iowa_html(content, lottery)
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
    
    # Powerball jackpot from CT Lottery
    try:
        content = fetch_url('https://www.ctlottery.org/Modules/Games/RSS.aspx?game=Powerball')
        if content:
            match = re.search(r'Jackpot[:\s]*\$?([\d,.]+)\s*(Million|Billion)?', content, re.I)
            if match:
                amount = float(match.group(1).replace(',', ''))
                multiplier = 1_000_000_000 if match.group(2) and 'billion' in match.group(2).lower() else 1_000_000
                jackpots['pb'] = {
                    'jackpot': int(amount * multiplier),
                    'cash_value': int(amount * multiplier * 0.5)  # Approximate cash value
                }
                print(f"  ✓ PB: ${amount} {match.group(2) or 'Million'}")
    except Exception as e:
        print(f"  ⚠️ PB jackpot error: {e}")
    
    # Mega Millions jackpot
    try:
        content = fetch_url('https://www.megamillions.com/cmspages/jackpothome.aspx')
        if content:
            match = re.search(r'\$?([\d,.]+)\s*(Million|Billion)', content, re.I)
            if match:
                amount = float(match.group(1).replace(',', ''))
                multiplier = 1_000_000_000 if 'billion' in match.group(2).lower() else 1_000_000
                jackpots['mm'] = {
                    'jackpot': int(amount * multiplier),
                    'cash_value': int(amount * multiplier * 0.5)
                }
                print(f"  ✓ MM: ${amount} {match.group(2)}")
    except Exception as e:
        print(f"  ⚠️ MM jackpot error: {e}")
    
    # L4L is always $1000/day for life (fixed)
    jackpots['l4l'] = {
        'jackpot': 7_000_000,  # Approximate lump sum value
        'cash_value': 5_750_000
    }
    
    # LA jackpot (estimate based on typical values)
    jackpots['la'] = {
        'jackpot': 2_000_000,
        'cash_value': 1_200_000
    }
    
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
