#!/usr/bin/env python3
"""
HONEST VALIDATION TEST - Walk-Forward Backtesting
Tests our methods on held-out data to get REAL improvement numbers.
"""

import json
from pathlib import Path
from collections import Counter
from itertools import combinations

DATA_DIR = Path(__file__).parent / 'data'

def load_draws(lottery):
    """Load historical draws."""
    for filename in [f'{lottery}_historical_data.json', f'{lottery}.json']:
        path = DATA_DIR / filename
        if path.exists():
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get('draws', [])
                return data
    return []

def calculate_random_baseline(max_num, pick_count, pool_size):
    """Calculate random baseline hit rate."""
    # If we pick pool_size numbers from max_num, chance of hitting any one number
    return pool_size / max_num

def validate_position_frequency(draws, train_ratio=0.8, pool_size=8):
    """
    Walk-forward validation of position frequency method.
    Train on first 80%, test on last 20%.
    """
    if len(draws) < 100:
        return None
    
    split_idx = int(len(draws) * train_ratio)
    train_draws = draws[split_idx:]  # Older draws (draws are newest-first)
    test_draws = draws[:split_idx]   # Newer draws
    
    # Build position pools from training data
    position_pools = [Counter() for _ in range(5)]
    for draw in train_draws:
        main_nums = sorted(draw.get('main', []))
        for i, num in enumerate(main_nums):
            if i < 5:
                position_pools[i][num] += 1
    
    # Get top numbers per position
    pools = []
    for counter in position_pools:
        top_nums = set(num for num, _ in counter.most_common(pool_size))
        pools.append(top_nums)
    
    # Test on held-out data
    hits = 0
    total = 0
    for draw in test_draws:
        main_nums = sorted(draw.get('main', []))
        for i, num in enumerate(main_nums):
            if i < 5:
                total += 1
                if num in pools[i]:
                    hits += 1
    
    accuracy = hits / total if total > 0 else 0
    return {
        'train_size': len(train_draws),
        'test_size': len(test_draws),
        'hits': hits,
        'total': total,
        'accuracy': accuracy,
        'accuracy_pct': f"{accuracy * 100:.2f}%"
    }

def validate_hot_numbers(draws, train_ratio=0.8, window=20, pool_size=10):
    """
    Walk-forward validation of hot numbers method.
    """
    if len(draws) < 100:
        return None
    
    split_idx = int(len(draws) * train_ratio)
    test_draws = draws[:split_idx]
    
    hits = 0
    total = 0
    
    # For each test draw, use the previous 'window' draws to build hot pool
    for i, draw in enumerate(test_draws):
        if i + window >= len(draws):
            break
        
        # Get window of draws before this one
        history = draws[i+1:i+1+window]
        
        # Count frequencies
        num_counter = Counter()
        for hist_draw in history:
            for num in hist_draw.get('main', []):
                num_counter[num] += 1
        
        hot_pool = set(num for num, _ in num_counter.most_common(pool_size))
        
        # Check hits
        for num in draw.get('main', []):
            total += 1
            if num in hot_pool:
                hits += 1
    
    accuracy = hits / total if total > 0 else 0
    return {
        'test_size': len(test_draws),
        'window': window,
        'pool_size': pool_size,
        'hits': hits,
        'total': total,
        'accuracy': accuracy,
        'accuracy_pct': f"{accuracy * 100:.2f}%"
    }

def validate_repeat_pattern(draws):
    """
    Validate the claim that 35-48% of numbers repeat from previous draw.
    """
    if len(draws) < 100:
        return None
    
    repeats = 0
    total = 0
    
    for i in range(len(draws) - 1):
        current = set(draws[i].get('main', []))
        previous = set(draws[i+1].get('main', []))
        
        repeat_count = len(current & previous)
        repeats += repeat_count
        total += len(current)
    
    repeat_rate = repeats / total if total > 0 else 0
    return {
        'draws_checked': len(draws) - 1,
        'total_numbers': total,
        'repeats': repeats,
        'repeat_rate': repeat_rate,
        'repeat_pct': f"{repeat_rate * 100:.2f}%"
    }

def validate_constraints(draws):
    """
    Validate that constraint filters capture 95% of winning tickets.
    """
    if len(draws) < 100:
        return None
    
    passed = 0
    total = len(draws)
    
    for draw in draws:
        main = sorted(draw.get('main', []))
        if len(main) != 5:
            continue
        
        # Check constraints
        ticket_sum = sum(main)
        decades = len(set(n // 10 for n in main))
        consecutive = sum(1 for i in range(4) if main[i+1] - main[i] == 1)
        odds = sum(1 for n in main if n % 2 == 1)
        
        # L4L constraints (adjust for each lottery)
        sum_ok = 65 <= ticket_sum <= 175
        decades_ok = decades >= 3
        consec_ok = consecutive <= 1
        odds_ok = 2 <= odds <= 3
        
        if sum_ok and decades_ok and consec_ok:
            passed += 1
    
    pass_rate = passed / total if total > 0 else 0
    return {
        'total': total,
        'passed': passed,
        'pass_rate': pass_rate,
        'pass_pct': f"{pass_rate * 100:.2f}%"
    }

def main():
    print("=" * 60)
    print("HONEST VALIDATION TEST - Walk-Forward Backtesting")
    print("=" * 60)
    
    results = {}
    
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        draws = load_draws(lottery)
        if not draws:
            print(f"\n{lottery.upper()}: No data found")
            continue
        
        print(f"\n{'=' * 60}")
        print(f"{lottery.upper()} - {len(draws)} draws")
        print("=" * 60)
        
        # Calculate random baseline
        max_nums = {'l4l': 48, 'la': 52, 'pb': 69, 'mm': 70}
        random_baseline = 8 / max_nums[lottery]  # Pool of 8 from max
        print(f"\nRandom baseline (pool of 8): {random_baseline * 100:.2f}%")
        
        # Position Frequency
        pos_result = validate_position_frequency(draws)
        if pos_result:
            improvement = pos_result['accuracy'] / random_baseline
            print(f"\n📊 POSITION FREQUENCY:")
            print(f"   Train: {pos_result['train_size']} draws, Test: {pos_result['test_size']} draws")
            print(f"   Hits: {pos_result['hits']}/{pos_result['total']}")
            print(f"   Accuracy: {pos_result['accuracy_pct']}")
            print(f"   vs Random: {improvement:.2f}x improvement")
            results[f'{lottery}_position'] = {
                **pos_result,
                'improvement': f"{improvement:.2f}x"
            }
        
        # Hot Numbers
        hot_result = validate_hot_numbers(draws)
        if hot_result:
            hot_baseline = 10 / max_nums[lottery]
            improvement = hot_result['accuracy'] / hot_baseline
            print(f"\n🔥 HOT NUMBERS (last 20 draws):")
            print(f"   Test: {hot_result['test_size']} draws")
            print(f"   Hits: {hot_result['hits']}/{hot_result['total']}")
            print(f"   Accuracy: {hot_result['accuracy_pct']}")
            print(f"   vs Random: {improvement:.2f}x improvement")
            results[f'{lottery}_hot'] = {
                **hot_result,
                'improvement': f"{improvement:.2f}x"
            }
        
        # Repeat Pattern
        repeat_result = validate_repeat_pattern(draws)
        if repeat_result:
            print(f"\n🔄 REPEAT PATTERN:")
            print(f"   Draws checked: {repeat_result['draws_checked']}")
            print(f"   Repeat rate: {repeat_result['repeat_pct']}")
            results[f'{lottery}_repeat'] = repeat_result
        
        # Constraint Validation
        const_result = validate_constraints(draws)
        if const_result:
            print(f"\n✅ CONSTRAINT FILTER:")
            print(f"   Total draws: {const_result['total']}")
            print(f"   Pass rate: {const_result['pass_pct']}")
            results[f'{lottery}_constraints'] = const_result
    
    # Save results
    output_file = DATA_DIR / 'validation_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n\n✅ Results saved to {output_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY - HONEST IMPROVEMENT FACTORS")
    print("=" * 60)
    for lottery in ['l4l', 'la', 'pb', 'mm']:
        pos_key = f'{lottery}_position'
        if pos_key in results:
            print(f"{lottery.upper()}: Position Frequency = {results[pos_key]['improvement']}")

if __name__ == '__main__':
    main()
