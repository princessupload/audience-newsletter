#!/usr/bin/env python3
"""
Lottery Audience Newsletter Generator
Helps audience build their own unique lottery tickets using data-driven methods.
Matches the Lottery Tracker app styling.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent / 'data'
OUTPUT_DIR = Path(__file__).parent / 'output'

# Oklahoma tax rates (24% federal + 4.75% state)
FEDERAL_TAX = 0.24
STATE_TAX = 0.0475
TOTAL_TAX_RATE = FEDERAL_TAX + STATE_TAX

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
        'best_methods': ['position_frequency', 'proven_combos', 'constraint_filter'],
        'constraints': {
            'sum_range': (65, 175),
            'min_decades': 3,
            'max_consecutive': 1,
            'odd_range': (2, 3),
            'high_range': (2, 3),
            'high_threshold': 25
        }
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
        'optimal_window': 400,
        'pattern_stability': 60.0,
        'best_methods': ['position_frequency', 'hot_10', 'constraint_filter'],
        'constraints': {
            'sum_range': (71, 188),
            'min_decades': 2,
            'max_consecutive': 1,
            'odd_range': (2, 3),
            'high_range': (2, 3),
            'high_threshold': 27
        }
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
        'best_methods': ['position_frequency', 'momentum', 'constraint_filter'],
        'constraints': {
            'sum_range': (80, 220),
            'min_decades': 3,
            'max_consecutive': 1,
            'odd_range': (2, 3),
            'high_range': (2, 3),
            'high_threshold': 35
        }
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
        'best_methods': ['hot_numbers', 'repeat_likelihood', 'momentum'],
        'constraints': {
            'sum_range': (100, 220),
            'min_decades': 3,
            'max_consecutive': 1,
            'odd_range': (2, 3),
            'high_range': (2, 3),
            'high_threshold': 36
        }
    }
}

def load_draws(lottery):
    """Load historical draws for a lottery."""
    for filename in [f'{lottery}_historical_data.json', f'{lottery}.json']:
        path = DATA_DIR / filename
        if path.exists():
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
                return data.get('draws', data) if isinstance(data, dict) else data
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
    if not amount:
        return 'N/A'
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    else:
        return f"${amount:,}"

def calculate_after_tax(cash_value):
    """Calculate after-tax amount for Oklahoma winner."""
    if not cash_value or cash_value <= 0:
        return 0
    return int(cash_value * (1 - TOTAL_TAX_RATE))

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
    current_time = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    current_date = datetime.now().strftime('%B %d, %Y')
    
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
            max-width: 900px;
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
        }}
        
        .date-badge {{
            background: linear-gradient(135deg, #B0E0E6 0%, #7DD3FC 100%);
            border: 3px solid #7DD3FC;
            border-radius: 20px;
            padding: 10px 25px;
            display: inline-block;
            margin-top: 15px;
            font-family: 'Libre Baskerville', serif;
            font-weight: 700;
            color: #000;
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
        
        .lottery-card {{
            background: linear-gradient(135deg, #fff0f5 0%, #f0f8ff 100%);
            border: 3px solid #7DD3FC;
            border-radius: 20px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(125, 211, 252, 0.3);
        }}
        
        .lottery-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 15px;
        }}
        
        .lottery-name {{
            font-family: 'Playfair Display', serif;
            font-size: 1.5em;
            color: #ff47bb;
        }}
        
        .strategy-badge {{
            background: linear-gradient(135deg, #ff47bb 0%, #ff75cc 100%);
            color: white;
            padding: 6px 15px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        
        .strategy-badge.next-draw {{
            background: linear-gradient(135deg, #7DD3FC 0%, #B0E0E6 100%);
            color: #000;
        }}
        
        .jackpot-info {{
            background: linear-gradient(135deg, #32CD32 0%, #228B22 100%);
            color: white;
            padding: 8px 15px;
            border-radius: 15px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .numbers-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
            margin: 15px 0;
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
            background: linear-gradient(135deg, #ffffff 0%, #f8f8f8 100%);
            border: 3px solid #ff47bb;
            color: #c2185b;
            box-shadow: 0 3px 10px rgba(255, 71, 187, 0.25);
        }}
        
        .ball.bonus {{
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
            border-color: #FF8C00;
            color: #5d4037;
        }}
        
        .ball.green {{
            background: linear-gradient(135deg, #90EE90 0%, #32CD32 100%);
            border-color: #228B22;
            color: #1b5e20;
        }}
        
        .plus {{
            font-size: 1.5em;
            color: #ff47bb;
            margin: 0 5px;
            font-weight: bold;
        }}
        
        .draw-info {{
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
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
            margin: 10px 0;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }}
        
        .pool-label {{
            font-weight: bold;
            color: #c2185b;
            min-width: 90px;
        }}
        
        .pool-numbers {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        
        .pool-num {{
            background: linear-gradient(135deg, #B0E0E6 0%, #7DD3FC 100%);
            color: #01579b;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.95em;
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
        
        .constraints-box {{
            background: #fffaf0;
            border: 2px solid #ffa500;
            border-radius: 12px;
            padding: 12px;
            margin-top: 15px;
            font-size: 0.9em;
        }}
        
        .constraints-title {{
            color: #ff8c00;
            font-weight: bold;
            margin-bottom: 8px;
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
        
        @media (max-width: 600px) {{
            h1 {{ font-size: 2em; }}
            .ball {{ width: 38px; height: 38px; font-size: 14px; }}
            .lottery-header {{ flex-direction: column; align-items: flex-start; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💖 LOTTERY NEWS 💖</h1>
            <p class="subtitle">Build Your Own Lucky Numbers</p>
            <div class="date-badge">📅 {current_date}</div>
        </div>
        
        <!-- LATEST DRAWINGS -->
        <div class="section">
            <h2 class="section-title">🎱 Latest Drawing Results</h2>
'''
    
    # Add latest drawings for each lottery
    for lottery_key in ['l4l', 'la', 'pb', 'mm']:
        config = LOTTERY_CONFIG[lottery_key]
        draws = draws_by_lottery.get(lottery_key, [])
        jp = jackpots.get(lottery_key, {})
        
        if not draws:
            continue
            
        latest = draws[0]
        main_nums = sorted(latest.get('main', []))
        bonus = latest.get('bonus', '?')
        draw_date = latest.get('date', 'Unknown')
        
        cash = jp.get('cash_value', 0)
        after_tax = calculate_after_tax(cash)
        jackpot_str = format_money(after_tax)
        
        balls_html = ''.join([f'<span class="ball">{n}</span>' for n in main_nums])
        
        strategy_class = 'next-draw' if config['strategy'] == 'NEXT_DRAW' else ''
        
        html += f'''
            <div class="lottery-card">
                <div class="lottery-header">
                    <span class="lottery-name">{config['emoji']} {config['name']}</span>
                    <span class="strategy-badge {strategy_class}">{config['strategy_desc']}</span>
                    <span class="jackpot-info">💰 {jackpot_str} after tax</span>
                </div>
                <div class="numbers-row">
                    {balls_html}
                    <span class="plus">+</span>
                    <span class="ball bonus">{bonus}</span>
                    <span style="margin-left: 10px; color: #666;">{config['bonus_name']}</span>
                </div>
                <div class="draw-info">📅 Draw Date: {draw_date}</div>
            </div>
'''
    
    html += '''
        </div>
        
        <!-- HOW TO BUILD YOUR TICKET -->
        <div class="section">
            <h2 class="section-title">🎯 How To Build Your Ticket</h2>
            
            <div class="how-to-box">
                <h3 class="how-to-title">📌 For HOLD Tickets (L4L, LA, PB)</h3>
                <ul class="how-to-list">
                    <li><strong>Pick 1 number</strong> from each Position Pool (1-5)</li>
                    <li><strong>Pick 1 bonus</strong> from the Bonus Pool</li>
                    <li><strong>Verify</strong> your ticket passes the constraints</li>
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
    
    # Add pools for each lottery
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
        
        html += f'''
            <div class="lottery-card">
                <div class="lottery-header">
                    <span class="lottery-name">{config['emoji']} {config['name']}</span>
                    <span class="strategy-badge {strategy_class}">{config['strategy_desc']}</span>
                </div>
                
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
                    <div class="pool-row" style="margin-top: 15px; padding-top: 10px; border-top: 1px dashed #F9A8D4;">
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
                    <div class="pool-title">🔄 Last Draw (35-48% repeat rate!)</div>
                    <div class="pool-numbers">{last_html}</div>
                </div>
                
                <div class="constraints-box">
                    <div class="constraints-title">✅ Ticket Constraints (verify your pick!)</div>
                    <div>• <strong>Sum Range:</strong> {constraints['sum_range'][0]} - {constraints['sum_range'][1]}</div>
                    <div>• <strong>Decades:</strong> At least {constraints['min_decades']} different (1-10, 11-20, etc.)</div>
                    <div>• <strong>Consecutive:</strong> Max {constraints['max_consecutive']} pair (like 12-13)</div>
                    <div>• <strong>Odd Numbers:</strong> {constraints['odd_range'][0]}-{constraints['odd_range'][1]} recommended</div>
                    <div>• <strong>High Numbers:</strong> {constraints['high_range'][0]}-{constraints['high_range'][1]} above {constraints['high_threshold']}</div>
                </div>
            </div>
'''
    
    html += f'''
        </div>
        
        <!-- CTA -->
        <div class="cta-box">
            <h3>✨ Want Live Analysis? ✨</h3>
            <p>Join us on Twitch and YouTube for drawing breakdowns!</p>
            <p style="margin-top: 12px; font-size: 1.1em;">
                <a href="https://twitch.tv/princessupload">📺 Twitch</a> &nbsp;|&nbsp; 
                <a href="https://youtube.com/@princessuploadie">▶️ YouTube</a>
            </p>
        </div>
        
        <div class="footer">
            <p>💖 With love from Princess Upload 💖</p>
            <p style="margin-top: 8px; font-size: 0.85em;">
                🎰 For entertainment purposes only • Generated {current_time} CT (Oklahoma)
            </p>
        </div>
    </div>
</body>
</html>'''
    
    return html

def generate_embed_snippet(draws_by_lottery, jackpots):
    """Generate simple embeddable HTML for Patreon/Substack."""
    current_date = datetime.now().strftime('%B %d, %Y')
    
    snippet = f'''<div style="font-family: Georgia, serif; max-width: 650px; margin: 0 auto; padding: 25px; background: linear-gradient(135deg, #fff0f5 0%, #f0f8ff 100%); border: 4px solid #ff47bb; border-radius: 20px;">
    <h2 style="color: #ff47bb; text-align: center; margin-bottom: 20px; font-size: 1.6em;">💖 LOTTERY UPDATE - {current_date} 💖</h2>
    
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
        after_tax = calculate_after_tax(cash)
        
        position_pools = generate_position_pools(draws, config['main_count'], config['optimal_window'])
        hot_numbers = get_hot_numbers(draws, window=20)[:6]
        
        nums_str = ' - '.join(map(str, main_nums))
        pools_str = ' | '.join([', '.join(map(str, p[:5])) for p in position_pools])
        hot_str = ', '.join(map(str, hot_numbers))
        
        snippet += f'''
    <div style="background: white; border: 3px solid #7DD3FC; border-radius: 15px; padding: 15px; margin: 15px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;">
            <strong style="color: #ff47bb; font-size: 1.2em;">{config['emoji']} {config['name']}</strong>
            <span style="background: #32CD32; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85em;">{format_money(after_tax)}</span>
        </div>
        <div style="margin: 10px 0;">
            <strong>Latest:</strong> {nums_str} + <span style="background: #FFD700; padding: 2px 8px; border-radius: 50%;">{bonus}</span>
        </div>
        <div style="font-size: 0.9em; color: #444; margin-top: 10px;">
            <div><strong>🔥 Hot:</strong> {hot_str}</div>
            <div style="margin-top: 5px;"><strong>Strategy:</strong> {config['strategy_desc']}</div>
        </div>
    </div>
'''
    
    snippet += '''
    <p style="text-align: center; margin-top: 20px; font-size: 0.95em;">
        💖 <a href="https://twitch.tv/princessupload" style="color: #ff47bb;">Twitch</a> | 
        <a href="https://youtube.com/@princessuploadie" style="color: #ff47bb;">YouTube</a> 💖
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
    date_str = datetime.now().strftime('%Y-%m-%d')
    
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
