#!/usr/bin/env python3
"""
Lottery Audience Newsletter Generator
Comprehensive newsletter with all lottery tracker features.
Helps audience build their own unique lottery tickets using data-driven methods.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter
import pytz

DATA_DIR = Path(__file__).parent / 'data'
OUTPUT_DIR = Path(__file__).parent / 'output'

# Tax rates by state
TAX_RATES = {
    'OK': {'federal': 0.24, 'state': 0.0475, 'name': 'Oklahoma'},
    'CA': {'federal': 0.24, 'state': 0.00, 'name': 'California'},  # CA doesn't tax lottery
    'MA': {'federal': 0.24, 'state': 0.05, 'name': 'Massachusetts'}
}

# Timezones (all 3 US continental zones)
TIMEZONES = {
    'PT': pytz.timezone('America/Los_Angeles'),  # Pacific Time
    'CT': pytz.timezone('America/Chicago'),      # Central Time
    'ET': pytz.timezone('America/New_York')      # Eastern Time
}

# Draw schedules (in Central Time) - CORRECT SCHEDULES
DRAW_SCHEDULES = {
    'l4l': {'days': None, 'schedule_text': 'Daily', 'time': '9:38 PM', 'name': 'Lucky for Life'},
    'la':  {'days': [1, 3, 6], 'schedule_text': 'Mon/Wed/Sat', 'time': '10:00 PM', 'name': 'Lotto America'},
    'pb':  {'days': [1, 3, 6], 'schedule_text': 'Mon/Wed/Sat', 'time': '9:59 PM', 'name': 'Powerball'},
    'mm':  {'days': [2, 5], 'schedule_text': 'Tue/Fri', 'time': '10:00 PM', 'name': 'Mega Millions'}
}

# Lottery configurations with best methods per lottery
LOTTERY_CONFIG = {
    'l4l': {
        'name': 'Lucky for Life',
        'emoji': '🍀',
        'bonus_name': 'Lucky Ball',
        'main_range': (1, 48),
        'bonus_range': (1, 18),
        'main_count': 5,
        'strategy': 'HOLD',
        'strategy_desc': 'Pick once, play FOREVER',
        'optimal_window': 400,
        'pattern_stability': 68.9,
        'best_methods': ['Position Frequency (40-44% stability)', 'Proven 3-Combos', 'Constraint Filter'],
        'grand_prize': '$7K/Week for Life',
        'fixed_cash': 5_750_000,
        'constraints': {
            'sum_range': (65, 175),
            'min_decades': 3,
            'max_consecutive': 1,
            'odd_range': (2, 3),
            'high_range': (2, 3),
            'high_threshold': 25
        },
        'color': '#ff47bb'
    },
    'la': {
        'name': 'Lotto America',
        'emoji': '⭐',
        'bonus_name': 'Star Ball',
        'main_range': (1, 52),
        'bonus_range': (1, 10),
        'main_count': 5,
        'strategy': 'HOLD',
        'strategy_desc': 'Pick once, play FOREVER',
        'optimal_window': 150,
        'pattern_stability': 60.0,
        'best_methods': ['Hot-10 Method (2.6x improvement)', 'Position Frequency', 'Constraint Filter'],
        'grand_prize': None,
        'constraints': {
            'sum_range': (71, 188),
            'min_decades': 2,
            'max_consecutive': 1,
            'odd_range': (2, 3),
            'high_range': (2, 3),
            'high_threshold': 27
        },
        'color': '#7DD3FC'
    },
    'pb': {
        'name': 'Powerball',
        'emoji': '🔴',
        'bonus_name': 'Powerball',
        'main_range': (1, 69),
        'bonus_range': (1, 26),
        'main_count': 5,
        'strategy': 'HOLD_REVIEW',
        'strategy_desc': 'Pick once, review every ~2 years',
        'optimal_window': 100,
        'pattern_stability': 46.7,
        'best_methods': ['Position+Momentum (1.21x)', 'Hot Pair Anchor (1.20x)', 'Mod-512 Filter (1.20x)'],
        'grand_prize': None,
        'constraints': {
            'sum_range': (80, 220),
            'min_decades': 3,
            'max_consecutive': 1,
            'odd_range': (2, 3),
            'high_range': (2, 3),
            'high_threshold': 35
        },
        'color': '#E31B23'
    },
    'mm': {
        'name': 'Mega Millions',
        'emoji': '💰',
        'bonus_name': 'Mega Ball',
        'main_range': (1, 70),
        'bonus_range': (1, 25),
        'main_count': 5,
        'strategy': 'NEXT_DRAW',
        'strategy_desc': 'Pick fresh EACH draw',
        'optimal_window': 30,
        'pattern_stability': None,
        'best_methods': ['Hot Numbers', 'Repeat Likelihood (35-48%)', 'Momentum Analysis'],
        'grand_prize': None,
        'constraints': {
            'sum_range': (100, 220),
            'min_decades': 3,
            'max_consecutive': 1,
            'odd_range': (2, 3),
            'high_range': (2, 3),
            'high_threshold': 36
        },
        'color': '#C0C0C0'
    }
}

# SVG Heart icon (perfect heart shape)
HEART_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="#ff47bb"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>'''

def load_draws(lottery):
    """Load historical draws for a lottery."""
    for filename in [f'{lottery}_historical_data.json', f'{lottery}.json']:
        path = DATA_DIR / filename
        if path.exists():
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get('draws', [])
                return data
    return []

def load_jackpots():
    """Load current jackpot data."""
    for filename in ['jackpots.json', 'jackpot_data.json']:
        path = DATA_DIR / filename
        if path.exists():
            with open(path, encoding='utf-8') as f:
                return json.load(f)
    return {}

def format_money(amount):
    """Format money with appropriate suffix."""
    if not amount or amount <= 0:
        return None
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    else:
        return f"${amount:,}"

def calculate_after_tax(cash_value, state='OK'):
    """Calculate after-tax amount for a specific state."""
    if not cash_value or cash_value <= 0:
        return 0
    rates = TAX_RATES.get(state, TAX_RATES['OK'])
    total_rate = rates['federal'] + rates['state']
    return int(cash_value * (1 - total_rate))

def get_times_string():
    """Get current time in all three US continental timezones."""
    now_utc = datetime.now(pytz.UTC)
    
    times = []
    for zone, tz in TIMEZONES.items():
        local_time = now_utc.astimezone(tz)
        time_str = local_time.strftime('%I:%M %p')
        times.append(f"{zone}: {time_str}")
    
    return ' | '.join(times)

def get_next_draw_info(lottery):
    """Calculate next draw date and countdown."""
    schedule = DRAW_SCHEDULES.get(lottery)
    if not schedule:
        return None, None
    
    now = datetime.now(TIMEZONES['CT'])
    
    # Handle Daily schedule (L4L)
    if schedule['days'] is None:
        # Daily - check if today's draw happened
        draw_hour = int(schedule['time'].split(':')[0])
        if 'PM' in schedule['time'] and draw_hour != 12:
            draw_hour += 12
        
        if now.hour < draw_hour:
            days_until = 0
        else:
            days_until = 1
    else:
        # Specific days
        draw_days = schedule['days']
        current_day = now.weekday()
        
        # Find next draw day
        days_until = None
        for d in sorted(draw_days):
            if d > current_day:
                days_until = d - current_day
                break
        if days_until is None:
            days_until = 7 - current_day + min(draw_days)
        
        # Check if draw is today and hasn't happened yet
        if current_day in draw_days:
            draw_hour = int(schedule['time'].split(':')[0])
            if 'PM' in schedule['time'] and draw_hour != 12:
                draw_hour += 12
            if now.hour < draw_hour:
                days_until = 0
    
    next_draw = now + timedelta(days=days_until)
    next_draw_str = next_draw.strftime('%A, %B %d')
    
    # Convert draw time to all 3 timezones
    draw_time_ct = schedule['time']
    # PT is 2 hours behind CT, ET is 1 hour ahead
    draw_hour = int(schedule['time'].split(':')[0])
    draw_min = schedule['time'].split(':')[1].split()[0]
    am_pm = 'PM' if 'PM' in schedule['time'] else 'AM'
    
    pt_hour = draw_hour - 2
    et_hour = draw_hour + 1
    if et_hour > 12:
        et_hour -= 12
    
    time_str = f"{pt_hour}:{draw_min} {am_pm} PT / {draw_hour}:{draw_min} {am_pm} CT / {et_hour}:{draw_min} {am_pm} ET"
    
    if days_until == 0:
        countdown = f"TODAY at {time_str}"
    elif days_until == 1:
        countdown = f"TOMORROW at {time_str}"
    else:
        countdown = f"In {days_until} days at {time_str}"
    
    return next_draw_str, countdown

def generate_position_pools(draws, main_count=5, window=400):
    """Generate position frequency pools from historical draws."""
    position_counters = [Counter() for _ in range(main_count)]
    
    for draw in draws[:window]:
        main_nums = sorted(draw.get('main', []))
        for i, num in enumerate(main_nums):
            if i < main_count:
                position_counters[i][num] += 1
    
    pools = []
    for counter in position_counters:
        top_nums = [num for num, _ in counter.most_common(8)]
        pools.append(top_nums)
    
    return pools

def generate_bonus_pool(draws, window=400, top_n=5):
    """Generate bonus ball frequency pool."""
    bonus_counter = Counter()
    for draw in draws[:window]:
        bonus = draw.get('bonus')
        if bonus:
            bonus_counter[bonus] += 1
    return [num for num, _ in bonus_counter.most_common(top_n)]

def get_hot_numbers(draws, window=20, top_n=10):
    """Get hot numbers from recent draws."""
    num_counter = Counter()
    for draw in draws[:window]:
        for num in draw.get('main', []):
            num_counter[num] += 1
    return [num for num, _ in num_counter.most_common(top_n)]

def get_last_draw_numbers(draws):
    """Get numbers from most recent draw (35-48% repeat rate)."""
    if draws:
        return sorted(draws[0].get('main', []))
    return []

def generate_newsletter_html(draws_by_lottery, jackpots):
    """Generate the full newsletter HTML matching lottery tracker styling."""
    now_utc = datetime.now(pytz.UTC)
    ok_time = now_utc.astimezone(TIMEZONES['CT'])
    current_date = ok_time.strftime('%B %d, %Y')
    times_str = get_times_string()
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lottery Newsletter - {current_date}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Cormorant+Garamond:wght@300;400;600&family=Libre+Baskerville:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Cormorant Garamond', Georgia, serif;
            background: linear-gradient(135deg, #F9A8D4 0%, #B0E0E6 50%, #ff75cc 100%);
            min-height: 100vh;
            padding: 20px;
            color: #000000;
            position: relative;
        }}
        
        body::before {{
            content: '';
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-image:
                radial-gradient(2px 2px at 20% 30%, rgba(255,255,255,0.9), transparent),
                radial-gradient(2px 2px at 60% 70%, rgba(255,255,255,0.8), transparent),
                radial-gradient(1px 1px at 50% 50%, rgba(255,255,255,0.7), transparent),
                radial-gradient(1px 1px at 80% 10%, rgba(255,255,255,0.7), transparent);
            background-size: 200% 200%;
            animation: sparkle 8s linear infinite;
            opacity: 0.6;
            pointer-events: none;
            z-index: 1;
        }}
        
        @keyframes sparkle {{
            0%, 100% {{ background-position: 0% 0%; }}
            50% {{ background-position: 100% 100%; }}
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            position: relative;
            z-index: 2;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            border: 4px solid #ff47bb;
            border-radius: 25px;
            padding: 30px;
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px rgba(255, 71, 187, 0.4);
        }}
        
        .heart-icon {{
            display: inline-block;
            width: 28px;
            height: 28px;
            vertical-align: middle;
            margin: 0 8px;
        }}
        
        .heart-icon svg {{
            width: 100%;
            height: 100%;
        }}
        
        h1 {{
            font-family: 'Playfair Display', serif;
            background: linear-gradient(135deg, #ff47bb 0%, #ff75cc 50%, #F9A8D4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.8em;
            margin-bottom: 10px;
            letter-spacing: 3px;
        }}
        
        .subtitle {{
            font-family: 'Libre Baskerville', serif;
            font-size: 1.2em;
            color: #ff47bb;
            font-style: italic;
            margin-bottom: 15px;
        }}
        
        .times-bar {{
            background: linear-gradient(135deg, #B0E0E6 0%, #7DD3FC 100%);
            border: 3px solid #7DD3FC;
            border-radius: 20px;
            padding: 12px 25px;
            display: inline-block;
            font-family: 'Libre Baskerville', serif;
            font-weight: 700;
            color: #000;
            font-size: 0.95em;
        }}
        
        .section {{
            background: rgba(255, 255, 255, 0.95);
            border: 4px solid #ff47bb;
            border-radius: 25px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px rgba(255, 71, 187, 0.3);
        }}
        
        .section-title {{
            font-family: 'Playfair Display', serif;
            font-size: 1.8em;
            color: #ff47bb;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #F9A8D4;
            text-align: center;
        }}
        
        .lottery-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}
        
        @media (max-width: 768px) {{
            .lottery-grid {{ grid-template-columns: 1fr; }}
        }}
        
        .lottery-card {{
            background: linear-gradient(135deg, #fff0f5 0%, #f0f8ff 100%);
            border: 4px solid;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .lottery-card.l4l {{ border-color: #ff47bb; }}
        .lottery-card.la {{ border-color: #7DD3FC; }}
        .lottery-card.pb {{ border-color: #E31B23; }}
        .lottery-card.mm {{ border-color: #C0C0C0; }}
        
        .lottery-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px dashed rgba(0,0,0,0.1);
        }}
        
        .lottery-name {{
            font-family: 'Playfair Display', serif;
            font-size: 1.4em;
            color: #ff47bb;
            flex-grow: 1;
        }}
        
        .draw-schedule {{
            font-size: 0.85em;
            color: #ff47bb;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .countdown {{
            background: linear-gradient(135deg, #FFEB3B 0%, #FFD700 100%);
            border: 3px solid #FFD700;
            border-radius: 15px;
            padding: 10px;
            text-align: center;
            font-weight: 700;
            margin-bottom: 12px;
            font-size: 0.95em;
        }}
        
        .countdown.soon {{
            background: linear-gradient(135deg, #ff47bb 0%, #ff75cc 100%);
            border-color: #ff47bb;
            color: white;
            animation: pulse 1s ease-in-out infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.02); }}
        }}
        
        .numbers-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
            margin: 12px 0;
            justify-content: center;
        }}
        
        .ball {{
            display: inline-flex;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 16px;
            background: linear-gradient(135deg, #7DD3FC 0%, #B0E0E6 100%);
            border: 3px solid rgba(0,0,0,0.2);
            color: #000;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
        }}
        
        .ball.bonus {{
            background: linear-gradient(135deg, #ff47bb 0%, #ff75cc 100%);
            border-color: #ff47bb;
            color: white;
        }}
        
        .plus {{
            font-size: 1.5em;
            color: #ff47bb;
            margin: 0 5px;
            font-weight: bold;
        }}
        
        .draw-date {{
            font-size: 0.9em;
            color: #666;
            text-align: center;
            margin-top: 8px;
        }}
        
        .jackpot-section {{
            background: linear-gradient(135deg, #87CEEB 0%, #B0E0E6 100%);
            border: 3px solid #87CEEB;
            border-radius: 15px;
            padding: 15px;
            margin: 12px 0;
            text-align: center;
        }}
        
        .jackpot-amount {{
            font-size: 1.8em;
            font-weight: 700;
            background: linear-gradient(135deg, #E31B23 0%, #ff47bb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-family: 'Playfair Display', serif;
        }}
        
        .jackpot-details {{
            font-size: 0.85em;
            color: #333;
            margin-top: 8px;
        }}
        
        .strategy-badge {{
            background: linear-gradient(135deg, #ff47bb 0%, #ff75cc 100%);
            color: white;
            padding: 6px 15px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 10px;
        }}
        
        .strategy-badge.next-draw {{
            background: linear-gradient(135deg, #7DD3FC 0%, #B0E0E6 100%);
            color: #000;
        }}
        
        .pool-section {{
            background: white;
            border: 2px dashed #F9A8D4;
            border-radius: 15px;
            padding: 15px;
            margin: 15px 0;
        }}
        
        .pool-title {{
            font-family: 'Libre Baskerville', serif;
            color: #ff47bb;
            font-weight: bold;
            margin-bottom: 12px;
            font-size: 1.1em;
        }}
        
        .pool-row {{
            margin: 8px 0;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 6px;
        }}
        
        .pool-label {{
            font-weight: bold;
            color: #c2185b;
            min-width: 85px;
            font-size: 0.9em;
        }}
        
        .pool-numbers {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }}
        
        .pool-num {{
            background: linear-gradient(135deg, #B0E0E6 0%, #7DD3FC 100%);
            color: #01579b;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            border: 2px solid #7DD3FC;
        }}
        
        .pool-num.hot {{
            background: linear-gradient(135deg, #FFB6C1 0%, #FF69B4 100%);
            border-color: #ff47bb;
            color: #880e4f;
        }}
        
        .pool-num.repeat {{
            background: linear-gradient(135deg, #98FB98 0%, #90EE90 100%);
            border-color: #32CD32;
            color: #1b5e20;
        }}
        
        .methods-box {{
            background: #fffaf0;
            border: 2px solid #ffa500;
            border-radius: 12px;
            padding: 12px;
            margin-top: 12px;
            font-size: 0.85em;
        }}
        
        .methods-title {{
            color: #ff8c00;
            font-weight: bold;
            margin-bottom: 6px;
        }}
        
        .constraints-box {{
            background: #f0fff0;
            border: 2px solid #32CD32;
            border-radius: 12px;
            padding: 12px;
            margin-top: 12px;
            font-size: 0.85em;
        }}
        
        .constraints-title {{
            color: #228B22;
            font-weight: bold;
            margin-bottom: 6px;
        }}
        
        .how-to-box {{
            background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
            border: 3px solid #4caf50;
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .how-to-title {{
            font-family: 'Playfair Display', serif;
            color: #2e7d32;
            font-size: 1.3em;
            margin-bottom: 15px;
        }}
        
        .how-to-list {{
            list-style: none;
            padding: 0;
        }}
        
        .how-to-list li {{
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
        }}
        
        .how-to-list li::before {{
            content: '✨';
            position: absolute;
            left: 0;
        }}
        
        .cta-box {{
            background: linear-gradient(135deg, #ff47bb 0%, #ff75cc 100%);
            color: white;
            text-align: center;
            padding: 25px;
            border-radius: 20px;
            margin: 25px 0;
            box-shadow: 0 6px 20px rgba(255, 71, 187, 0.4);
        }}
        
        .cta-box h3 {{
            font-family: 'Playfair Display', serif;
            font-size: 1.5em;
            margin-bottom: 12px;
        }}
        
        .cta-box a {{
            color: white;
            text-decoration: underline;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span class="heart-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#ff47bb"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg></span>
                Build Your Own Tickets
                <span class="heart-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#ff47bb"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg></span>
            </h1>
            <p class="subtitle">Build Your Own Lucky Numbers with Data-Driven Pools</p>
            <div class="times-bar">📅 {current_date} | 🕐 {times_str}</div>
        </div>
        
        <!-- LATEST DRAWINGS -->
        <div class="section">
            <h2 class="section-title">🎱 Latest Drawing Results</h2>
            <div class="lottery-grid">
'''
    
    # Add lottery cards
    for lottery_key in ['l4l', 'la', 'pb', 'mm']:
        config = LOTTERY_CONFIG[lottery_key]
        draws = draws_by_lottery.get(lottery_key, [])
        jp = jackpots.get(lottery_key, {})
        schedule = DRAW_SCHEDULES.get(lottery_key, {})
        
        if not draws:
            continue
            
        latest = draws[0]
        main_nums = sorted(latest.get('main', []))
        bonus = latest.get('bonus', '?')
        draw_date = latest.get('date', 'Unknown')
        
        # Draw info
        next_draw, countdown = get_next_draw_info(lottery_key)
        schedule_text = schedule.get('schedule_text', 'TBD')
        
        # Jackpot info - show jackpot, cash value, and after-tax (federal 24% + OK 4.75%)
        jackpot_html = ''
        
        if config.get('grand_prize'):
            # L4L has fixed prize structure
            fixed_cash = config.get('fixed_cash', 5_750_000)
            after_tax = calculate_after_tax(fixed_cash, 'OK')
            jackpot_html = f'''
                <div class="jackpot-section">
                    <div class="jackpot-amount">{config['grand_prize']}</div>
                    <div class="jackpot-details">
                        <div><strong>Cash Option:</strong> {format_money(fixed_cash)}</div>
                        <div><strong>After Taxes (24% Fed + 4.75% OK):</strong> {format_money(after_tax)}</div>
                    </div>
                </div>
'''
        else:
            jackpot_amt = jp.get('jackpot', 0)
            cash = jp.get('cash_value', 0)
            if jackpot_amt and jackpot_amt > 0:
                after_tax = calculate_after_tax(cash, 'OK') if cash else 0
                jackpot_html = f'''
                <div class="jackpot-section">
                    <div class="jackpot-amount">{format_money(jackpot_amt)}</div>
                    <div class="jackpot-details">
                        <div><strong>Cash Option:</strong> {format_money(cash) if cash else 'TBD'}</div>
                        <div><strong>After Taxes (24% Fed + 4.75% OK):</strong> {format_money(after_tax) if after_tax else 'TBD'}</div>
                    </div>
                </div>
'''
        
        balls_html = ''.join([f'<span class="ball">{n}</span>' for n in main_nums])
        
        countdown_class = 'soon' if countdown and 'TODAY' in countdown else ''
        
        html += f'''
                <div class="lottery-card {lottery_key}">
                    <div class="lottery-header">
                        <span class="lottery-name">{config['emoji']} {config['name']}</span>
                    </div>
                    <div class="draw-schedule">📆 Draws: {schedule_text} at {schedule.get('time', 'TBD')} CT</div>
                    <div class="countdown {countdown_class}">⏰ Next: {countdown or 'TBD'}</div>
                    {jackpot_html}
                    <div class="numbers-row">
                        {balls_html}
                        <span class="plus">+</span>
                        <span class="ball bonus">{bonus}</span>
                    </div>
                    <div class="draw-date">📅 Last Draw: {draw_date}</div>
                </div>
'''
    
    html += '''
            </div>
        </div>
        
        <!-- HOW TO BUILD YOUR TICKET -->
        <div class="section">
            <h2 class="section-title">🎯 How To Build Your Ticket</h2>
            
            <div class="how-to-box">
                <h3 class="how-to-title">📌 For HOLD Tickets (L4L, LA, PB)</h3>
                <ul class="how-to-list">
                    <li><strong>Pick 1 number</strong> from each Position Pool (1-5)</li>
                    <li><strong>Pick 1 bonus</strong> from the Bonus Pool</li>
                    <li><strong>Verify</strong> your ticket passes the constraints below</li>
                    <li><strong>Play the SAME ticket</strong> every draw - patterns are stable!</li>
                </ul>
            </div>
            
            <div class="how-to-box" style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-color: #2196f3;">
                <h3 class="how-to-title" style="color: #1565c0;">🌟 For NEXT DRAW Tickets (MM, or any lottery)</h3>
                <ul class="how-to-list">
                    <li><strong>Include 1-2 numbers</strong> from "Last Draw" (35-48% repeat!)</li>
                    <li><strong>Add 2-3 numbers</strong> from "Hot Numbers" pool</li>
                    <li><strong>Fill remaining</strong> from Position Pools</li>
                    <li><strong>Generate FRESH</strong> each draw - momentum matters!</li>
                </ul>
            </div>
        </div>
        
        <!-- NUMBER POOLS PER LOTTERY -->
        <div class="section">
            <h2 class="section-title">🔢 Number Pools By Lottery</h2>
'''
    
    # Add detailed pools for each lottery
    for lottery_key in ['l4l', 'la', 'pb', 'mm']:
        config = LOTTERY_CONFIG[lottery_key]
        draws = draws_by_lottery.get(lottery_key, [])
        
        if not draws:
            continue
        
        # Generate pools
        position_pools = generate_position_pools(draws, config['main_count'], config['optimal_window'])
        bonus_pool = generate_bonus_pool(draws, config['optimal_window'])
        hot_numbers = get_hot_numbers(draws, window=20)
        last_draw = get_last_draw_numbers(draws)
        constraints = config['constraints']
        
        strategy_class = 'next-draw' if config['strategy'] == 'NEXT_DRAW' else ''
        stability_str = f"{config['pattern_stability']}% stable" if config['pattern_stability'] else 'Use NEXT DRAW method'
        
        html += f'''
            <div class="lottery-card {lottery_key}" style="margin: 20px 0;">
                <div class="lottery-header">
                    <span class="lottery-name">{config['emoji']} {config['name']}</span>
                </div>
                <div class="strategy-badge {strategy_class}">{config['strategy_desc']} ({stability_str})</div>
                
                <div class="pool-section">
                    <div class="pool-title">📊 Position Pools (pick 1 from each)</div>
'''
        
        for i, pool in enumerate(position_pools):
            pool_html = ''.join([f'<span class="pool-num">{n}</span>' for n in pool])
            html += f'''
                    <div class="pool-row">
                        <span class="pool-label">Position {i+1}:</span>
                        <div class="pool-numbers">{pool_html}</div>
                    </div>
'''
        
        bonus_html = ''.join([f'<span class="pool-num">{n}</span>' for n in bonus_pool])
        html += f'''
                    <div class="pool-row" style="margin-top: 12px; padding-top: 10px; border-top: 1px dashed #F9A8D4;">
                        <span class="pool-label">{config['bonus_name']}:</span>
                        <div class="pool-numbers">{bonus_html}</div>
                    </div>
                </div>
'''
        
        # Hot numbers and last draw
        hot_html = ''.join([f'<span class="pool-num hot">{n}</span>' for n in hot_numbers[:8]])
        last_html = ''.join([f'<span class="pool-num repeat">{n}</span>' for n in last_draw])
        
        html += f'''
                <div class="pool-section">
                    <div class="pool-title">🔥 Hot Numbers (last 20 draws)</div>
                    <div class="pool-numbers">{hot_html}</div>
                </div>
                
                <div class="pool-section">
                    <div class="pool-title">🔄 Last Draw Numbers (35-48% repeat rate!)</div>
                    <div class="pool-numbers">{last_html}</div>
                </div>
                
                <div class="methods-box">
                    <div class="methods-title">🧪 Best Methods for {config['name']}</div>
                    <div>{'  •  '.join(config['best_methods'])}</div>
                </div>
                
                <div class="constraints-box">
                    <div class="constraints-title">✅ Verify Your Ticket</div>
                    <div>• <strong>Sum:</strong> {constraints['sum_range'][0]} - {constraints['sum_range'][1]}</div>
                    <div>• <strong>Decades:</strong> At least {constraints['min_decades']} different</div>
                    <div>• <strong>Consecutive:</strong> Max {constraints['max_consecutive']} pair</div>
                    <div>• <strong>Odd/Even:</strong> {constraints['odd_range'][0]}-{constraints['odd_range'][1]} odd numbers</div>
                    <div>• <strong>High ({constraints['high_threshold']}+):</strong> {constraints['high_range'][0]}-{constraints['high_range'][1]} numbers</div>
                </div>
            </div>
'''
    
    html += f'''
        </div>
        
        <!-- CTA -->
        <div class="cta-box">
            <h3>
                <span class="heart-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg></span>
                Want Live Analysis?
                <span class="heart-icon"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg></span>
            </h3>
            <p>Join us on Twitch and YouTube for drawing breakdowns!</p>
            <p style="margin-top: 12px; font-size: 1.1em;">
                <a href="https://twitch.tv/princessupload">📺 Twitch</a> &nbsp;|&nbsp; 
                <a href="https://youtube.com/@princessuploadie">▶️ YouTube</a>
            </p>
        </div>
        
        <div class="footer">
            <p>
                <span class="heart-icon" style="width: 20px; height: 20px;"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#ff47bb"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg></span>
                With love from Princess Upload
                <span class="heart-icon" style="width: 20px; height: 20px;"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#ff47bb"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg></span>
            </p>
            <p style="margin-top: 10px; font-size: 0.85em; color: #888;">
                🎰 For entertainment purposes only
            </p>
            <p style="margin-top: 5px; font-size: 0.8em; color: #aaa;">
                Generated: {times_str}
            </p>
        </div>
    </div>
</body>
</html>'''
    
    return html

def generate_embed_snippet(draws_by_lottery, jackpots):
    """Generate simple embeddable HTML for Patreon/Substack."""
    now_utc = datetime.now(pytz.UTC)
    ok_time = now_utc.astimezone(TIMEZONES['CT'])
    current_date = ok_time.strftime('%B %d, %Y')
    
    snippet = f'''<div style="font-family: Georgia, serif; max-width: 650px; margin: 0 auto; padding: 25px; background: linear-gradient(135deg, #fff0f5 0%, #f0f8ff 100%); border: 4px solid #ff47bb; border-radius: 20px;">
    <h2 style="color: #ff47bb; text-align: center; margin-bottom: 20px; font-size: 1.6em;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="#ff47bb" style="vertical-align: middle;"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
        LOTTERY UPDATE - {current_date}
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="#ff47bb" style="vertical-align: middle;"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
    </h2>
    
    <p style="text-align: center; margin-bottom: 20px; color: #666;">Build your own unique ticket using these data-driven pools!</p>
'''
    
    for lottery_key in ['l4l', 'la', 'pb', 'mm']:
        config = LOTTERY_CONFIG[lottery_key]
        draws = draws_by_lottery.get(lottery_key, [])
        jp = jackpots.get(lottery_key, {})
        
        if not draws:
            continue
            
        latest = draws[0]
        main_nums = sorted(latest.get('main', []))
        bonus = latest.get('bonus', '?')
        
        cash = jp.get('cash_value', 0)
        jackpot_str = ''
        if config.get('grand_prize'):
            jackpot_str = config['grand_prize']
        elif cash and cash > 0:
            jackpot_str = format_money(calculate_after_tax(cash, 'OK')) + ' (OK after tax)'
        
        hot_numbers = get_hot_numbers(draws, window=20)[:6]
        
        nums_str = ' - '.join(map(str, main_nums))
        hot_str = ', '.join(map(str, hot_numbers))
        
        jackpot_badge = ''
        if jackpot_str:
            jackpot_badge = f'<span style="float: right; background: #32CD32; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.8em;">{jackpot_str}</span>'
        
        snippet += f'''
    <div style="background: white; border: 3px solid #7DD3FC; border-radius: 15px; padding: 15px; margin: 15px 0;">
        <div style="margin-bottom: 10px;">
            <strong style="color: #ff47bb; font-size: 1.2em;">{config['emoji']} {config['name']}</strong>
            {jackpot_badge}
        </div>
        <div style="margin: 10px 0; font-size: 1.1em;">
            <strong>Latest:</strong> {nums_str} + <span style="background: linear-gradient(135deg, #ff47bb, #ff75cc); color: white; padding: 3px 8px; border-radius: 50%;">{bonus}</span>
        </div>
        <div style="font-size: 0.9em; color: #444; margin-top: 10px;">
            <div><strong>🔥 Hot:</strong> {hot_str}</div>
            <div style="margin-top: 5px;"><strong>Strategy:</strong> {config['strategy_desc']}</div>
        </div>
    </div>
'''
    
    snippet += '''
    <p style="text-align: center; margin-top: 20px; font-size: 0.95em;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="#ff47bb" style="vertical-align: middle;"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
        <a href="https://twitch.tv/princessupload" style="color: #ff47bb;">Twitch</a> | 
        <a href="https://youtube.com/@princessuploadie" style="color: #ff47bb;">YouTube</a>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="#ff47bb" style="vertical-align: middle;"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
    </p>
    <p style="text-align: center; font-size: 0.8em; color: #888; margin-top: 10px;">For entertainment purposes only</p>
</div>'''
    
    return snippet

def main():
    """Generate all newsletter outputs."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Load all data
    draws_by_lottery = {}
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        draws_by_lottery[lottery] = load_draws(lottery)
        print(f"📊 Loaded {len(draws_by_lottery[lottery])} draws for {lottery.upper()}")
    
    jackpots = load_jackpots()
    
    # Generate full newsletter
    full_html = generate_newsletter_html(draws_by_lottery, jackpots)
    
    now_utc = datetime.now(pytz.UTC)
    ok_time = now_utc.astimezone(TIMEZONES['CT'])
    date_str = ok_time.strftime('%Y-%m-%d')
    
    # Save dated version
    dated_file = OUTPUT_DIR / f'newsletter_{date_str}.html'
    with open(dated_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"✅ Newsletter saved: {dated_file}")
    
    # Save as latest.html
    latest_file = OUTPUT_DIR / 'latest.html'
    with open(latest_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"✅ Latest saved: {latest_file}")
    
    # Generate embed snippet
    embed_html = generate_embed_snippet(draws_by_lottery, jackpots)
    embed_file = OUTPUT_DIR / 'embed_snippet.html'
    with open(embed_file, 'w', encoding='utf-8') as f:
        f.write(embed_html)
    print(f"✅ Embed snippet saved: {embed_file}")
    
    print(f"\n🎉 Newsletter generation complete!")
    print(f"   Preview: Open {latest_file} in your browser")
    print(f"   Embed: Copy contents of {embed_file} into Patreon/Substack")

if __name__ == '__main__':
    main()
