"""Audit pool sizes and numbers for maximum odds improvement."""
import json
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'

LOTTERIES = {
    'l4l': {'file': 'l4l.json', 'main_range': 48, 'bonus_range': 18, 'name': 'Lucky for Life'},
    'la': {'file': 'la.json', 'main_range': 52, 'bonus_range': 10, 'name': 'Lotto America'},
    'pb': {'file': 'pb.json', 'main_range': 69, 'bonus_range': 26, 'name': 'Powerball'},
    'mm': {'file': 'mm.json', 'main_range': 70, 'bonus_range': 25, 'name': 'Mega Millions'}
}

def analyze_lottery(lottery_key, info):
    """Analyze pool accuracy for a lottery."""
    data_file = DATA_DIR / info['file']
    if not data_file.exists():
        print(f"{info['name']}: DATA FILE NOT FOUND")
        return None
    
    with open(data_file) as f:
        data = json.load(f)
    
    # Handle both formats: direct list or dict with 'draws' key
    if isinstance(data, dict) and 'draws' in data:
        draws = data['draws']
    elif isinstance(data, list):
        draws = data
    else:
        print(f"{info['name']}: UNKNOWN DATA FORMAT")
        return None
    
    total_draws = len(draws)
    main_range = info['main_range']
    bonus_range = info['bonus_range']
    random_per_pos = 100 / main_range
    random_bonus = 100 / bonus_range
    
    print(f"\n{'='*60}")
    print(f"{info['name'].upper()} ({total_draws} draws)")
    print(f"{'='*60}")
    print(f"Random baseline: {random_per_pos:.2f}% per position, {random_bonus:.2f}% bonus")
    
    # Generate position frequency pools using ALL data (HOLD strategy)
    position_counters = [Counter() for _ in range(5)]
    for draw in draws:
        main_nums = sorted(draw.get('main', []))
        for i, num in enumerate(main_nums):
            if i < 5:
                position_counters[i][num] += 1
    
    print(f"\n--- Position Pools (ALL {total_draws} draws for HOLD) ---")
    
    results = {'pools': [], 'improvements': []}
    
    for pos, counter in enumerate(position_counters):
        # Test different pool sizes to find optimal
        best_pool_size = 8
        best_improvement = 0
        
        for pool_size in [6, 8, 10, 12]:
            top_n = counter.most_common(pool_size)
            coverage = sum(c for _, c in top_n) / total_draws * 100
            improvement = coverage / random_per_pos
            
            # We want high coverage but not too large pools (diminishing returns)
            # Efficiency = improvement per pool number
            efficiency = improvement / pool_size
            
            if pool_size == 8:
                best_improvement = improvement
        
        # Use pool size 8 as our standard
        top_8 = counter.most_common(8)
        nums_8 = sorted([n for n, _ in top_8])
        coverage_8 = sum(c for _, c in top_8) / total_draws * 100
        improvement_8 = coverage_8 / random_per_pos
        
        # Also show top 10 for comparison
        top_10 = counter.most_common(10)
        coverage_10 = sum(c for _, c in top_10) / total_draws * 100
        improvement_10 = coverage_10 / random_per_pos
        
        print(f"\nPosition {pos+1}:")
        print(f"  Top 8:  {nums_8}")
        print(f"          Coverage: {coverage_8:.1f}% = {improvement_8:.2f}x improvement")
        print(f"  Top 10: Coverage: {coverage_10:.1f}% = {improvement_10:.2f}x improvement")
        
        # Show the actual frequency counts
        print(f"  Frequencies: {[(n, c) for n, c in top_8]}")
        
        results['pools'].append(nums_8)
        results['improvements'].append(improvement_8)
    
    avg_improvement = sum(results['improvements']) / 5
    print(f"\n>>> AVERAGE POSITION IMPROVEMENT: {avg_improvement:.2f}x <<<")
    
    # Bonus ball analysis
    bonus_counter = Counter()
    for draw in draws:
        bonus = draw.get('bonus')
        if bonus:
            bonus_counter[bonus] += 1
    
    top_5_bonus = bonus_counter.most_common(5)
    top_8_bonus = bonus_counter.most_common(8)
    
    coverage_5 = sum(c for _, c in top_5_bonus) / total_draws * 100
    coverage_8 = sum(c for _, c in top_8_bonus) / total_draws * 100
    
    bonus_nums_5 = sorted([n for n, _ in top_5_bonus])
    bonus_nums_8 = sorted([n for n, _ in top_8_bonus])
    
    improvement_5 = coverage_5 / random_bonus
    improvement_8 = coverage_8 / random_bonus
    
    print(f"\n--- Bonus Pool ---")
    print(f"  Top 5:  {bonus_nums_5} = {coverage_5:.1f}% ({improvement_5:.2f}x)")
    print(f"  Top 8:  {bonus_nums_8} = {coverage_8:.1f}% ({improvement_8:.2f}x)")
    print(f"  Frequencies: {[(n, c) for n, c in top_5_bonus]}")
    
    results['bonus_pool'] = bonus_nums_5
    results['bonus_improvement'] = improvement_5
    results['avg_improvement'] = avg_improvement
    
    return results

if __name__ == '__main__':
    print("POOL ACCURACY AUDIT")
    print("=" * 60)
    
    all_results = {}
    for lottery_key, info in LOTTERIES.items():
        results = analyze_lottery(lottery_key, info)
        if results:
            all_results[lottery_key] = results
    
    print("\n" + "=" * 60)
    print("SUMMARY - OPTIMAL POOLS FOR MAXIMUM IMPROVEMENT")
    print("=" * 60)
    
    for lottery_key, results in all_results.items():
        name = LOTTERIES[lottery_key]['name']
        print(f"\n{name}:")
        print(f"  Avg Position Improvement: {results['avg_improvement']:.2f}x")
        print(f"  Bonus Improvement: {results['bonus_improvement']:.2f}x")
        for i, pool in enumerate(results['pools']):
            print(f"  Pos {i+1}: {pool}")
        print(f"  Bonus: {results['bonus_pool']}")
