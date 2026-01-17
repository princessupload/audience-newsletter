#!/usr/bin/env python3
"""
Data Updater for Lottery Audience Newsletter
Syncs data from the verified lottery-guide repository (dual-source verified).
Also fetches live jackpot data from official sources.
"""

import json
import re
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
LOTTERY_GUIDE_DIR = BASE_DIR.parent / 'lottery-guide'

# Mapping of lottery keys to data files in lottery-guide
LOTTERY_FILES = {
    'l4l': 'l4l_historical_data.json',
    'la': 'la_historical_data.json',
    'pb': 'pb_historical_data.json',
    'mm': 'mm_historical_data.json'
}

def fetch_url(url):
    """Fetch URL content with proper headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate'
    }
    
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

def sync_lottery_data():
    """Sync lottery draw data from lottery-guide repository."""
    print("\n📊 Syncing lottery data from lottery-guide...")
    
    if not LOTTERY_GUIDE_DIR.exists():
        print(f"  ❌ lottery-guide directory not found: {LOTTERY_GUIDE_DIR}")
        return False
    
    DATA_DIR.mkdir(exist_ok=True)
    
    for lottery_key, filename in LOTTERY_FILES.items():
        source_file = LOTTERY_GUIDE_DIR / filename
        dest_file = DATA_DIR / f'{lottery_key}.json'
        
        if not source_file.exists():
            print(f"  ⚠️ {lottery_key.upper()}: Source file not found")
            continue
        
        # Load source data
        with open(source_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)
        
        draws = source_data.get('draws', [])
        
        # Validate data - check for duplicates in numbers (bad data indicator)
        valid_draws = []
        for draw in draws:
            main = draw.get('main', [])
            if len(main) == len(set(main)):  # No duplicates
                valid_draws.append(draw)
            else:
                print(f"  ⚠️ Skipping invalid draw with duplicates: {draw}")
        
        # Sort by date (newest first)
        valid_draws.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        # Save to newsletter data directory
        output_data = {
            'draws': valid_draws,
            'synced_from': str(source_file),
            'synced_at': datetime.now().isoformat(),
            'total_draws': len(valid_draws)
        }
        
        with open(dest_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        latest = valid_draws[0] if valid_draws else None
        if latest:
            print(f"  ✅ {lottery_key.upper()}: {len(valid_draws)} draws (latest: {latest['date']} - {latest['main']} + {latest['bonus']})")
        else:
            print(f"  ⚠️ {lottery_key.upper()}: No valid draws")
    
    return True

def update_jackpots():
    """Fetch live jackpot data from official sources."""
    print("\n💰 Updating jackpots...")
    
    jackpots = {}
    
    # Try to load jackpots from lottery-guide first (most reliable)
    guide_jackpots = LOTTERY_GUIDE_DIR / 'jackpot_data.json'
    if guide_jackpots.exists():
        try:
            with open(guide_jackpots, 'r') as f:
                guide_data = json.load(f)
            
            # Copy jackpot data if available
            for key in ['pb', 'mm', 'la', 'l4l']:
                if key in guide_data:
                    jp = guide_data[key]
                    # Handle different key formats
                    jackpot_val = jp.get('advertised') or jp.get('amount') or jp.get('jackpot', 0)
                    cash_val = jp.get('cashOption') or jp.get('cashValue') or jp.get('cash_value', 0)
                    
                    # Handle string jackpot (like L4L "$7K/week for life")
                    if isinstance(jackpot_val, str):
                        jackpot_val = 7_000_000  # L4L approximate lump sum
                    
                    jackpots[key] = {
                        'jackpot': jackpot_val,
                        'cash_value': cash_val
                    }
                    amt = jackpot_val / 1_000_000 if jackpot_val else 0
                    print(f"  ✅ {key.upper()}: ${amt:.1f}M (from lottery-guide)")
        except Exception as e:
            print(f"  ⚠️ Could not load lottery-guide jackpots: {e}")
    
    # Fetch live jackpots for any missing
    if 'pb' not in jackpots:
        try:
            content = fetch_url('https://www.valottery.com/data/draw-games/powerball')
            if content:
                match = re.search(r'\$(\d+)\s*MILLION', content, re.IGNORECASE)
                if match:
                    amount = int(match.group(1))
                    cash_match = re.search(r'Cash\s*Value[:\s]*\$(\d+)', content, re.IGNORECASE)
                    cash = int(cash_match.group(1)) * 1_000_000 if cash_match else int(amount * 450_000)
                    jackpots['pb'] = {'jackpot': amount * 1_000_000, 'cash_value': cash}
                    print(f"  ✅ PB: ${amount}M (from Virginia Lottery)")
        except Exception as e:
            print(f"  ⚠️ PB fetch error: {e}")
    
    if 'mm' not in jackpots:
        try:
            content = fetch_url('https://www.valottery.com/data/draw-games/megamillions')
            if content:
                match = re.search(r'\$(\d+)\s*MILLION', content, re.IGNORECASE)
                if match:
                    amount = int(match.group(1))
                    cash_match = re.search(r'Cash\s*Value[:\s]*\$(\d+)', content, re.IGNORECASE)
                    cash = int(cash_match.group(1)) * 1_000_000 if cash_match else int(amount * 457_000)
                    jackpots['mm'] = {'jackpot': amount * 1_000_000, 'cash_value': cash}
                    print(f"  ✅ MM: ${amount}M (from Virginia Lottery)")
        except Exception as e:
            print(f"  ⚠️ MM fetch error: {e}")
    
    if 'la' not in jackpots:
        try:
            content = fetch_url('https://www.powerball.com/lotto-america')
            if content:
                match = re.search(r'\$([\d.]+)\s*M', content)
                if match:
                    amount = float(match.group(1))
                    jackpots['la'] = {'jackpot': int(amount * 1_000_000), 'cash_value': int(amount * 450_000)}
                    print(f"  ✅ LA: ${amount}M (from powerball.com)")
        except Exception as e:
            print(f"  ⚠️ LA fetch error: {e}")
    
    # Set defaults for any still missing
    if 'pb' not in jackpots:
        jackpots['pb'] = {'jackpot': 179_000_000, 'cash_value': 80_550_000}
        print(f"  ⚠️ PB: Using fallback estimate")
    
    if 'mm' not in jackpots:
        jackpots['mm'] = {'jackpot': 250_000_000, 'cash_value': 113_500_000}
        print(f"  ⚠️ MM: Using fallback estimate")
    
    if 'la' not in jackpots:
        jackpots['la'] = {'jackpot': 12_740_000, 'cash_value': 6_370_000}
        print(f"  ⚠️ LA: Using fallback estimate")
    
    # L4L is always fixed
    jackpots['l4l'] = {'jackpot': 7_000_000, 'cash_value': 5_750_000}
    
    # Save jackpots
    jackpot_file = DATA_DIR / 'jackpots.json'
    with open(jackpot_file, 'w', encoding='utf-8') as f:
        json.dump(jackpots, f, indent=2)
    
    print(f"  ✅ Jackpots saved to {jackpot_file}")
    return True

def main():
    """Run full data update."""
    print("=" * 60)
    print("🎰 LOTTERY NEWSLETTER DATA SYNC")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Sync lottery draw data from lottery-guide (verified source)
    sync_lottery_data()
    
    # Update jackpots
    update_jackpots()
    
    print("\n" + "=" * 60)
    print("✅ Data sync complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
