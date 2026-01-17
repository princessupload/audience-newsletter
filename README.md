# 🎰 Lottery Audience Newsletter

A private newsletter system that helps your audience build their own unique lottery tickets using data-driven position pools and proven methods.

## Features

- **Position Frequency Pools**: Top numbers for each sorted position based on historical data
- **Hot Number Tracking**: Numbers appearing frequently in recent draws
- **Repeat Likelihood**: Last draw numbers (35-48% repeat rate historically)
- **Constraint Guidance**: Sum ranges, decade distribution, consecutive rules
- **Auto-Updates**: GitHub Actions fetches new drawings daily
- **Embeddable HTML**: Ready to paste into Patreon, Substack, or any website

## Lotteries Covered

| Lottery | Strategy | Data Window | Update Frequency |
|---------|----------|-------------|------------------|
| Lucky for Life | HOLD (pick once, play forever) | 400+ draws | Daily |
| Lotto America | HOLD (pick once, play forever) | 400+ draws | Mon/Wed/Sat |
| Powerball | HOLD + Review (every ~2 years) | 400+ draws | Mon/Wed/Sat |
| Mega Millions | NEXT DRAW (pick fresh each time) | 30 draws | Tue/Fri |

## How Audience Uses This

1. **For HOLD Tickets**: Pick 1 number from each position pool, add bonus from bonus pool
2. **For NEXT DRAW Tickets**: Include 1-2 numbers from last draw (likely repeats) + hot numbers
3. **Always**: Verify ticket passes constraints (sum range, decades, etc.)

## Files

- `generate_newsletter.py` - Main generator script
- `data/` - Historical drawings for all lotteries
- `output/` - Generated newsletter HTML files
- `.github/workflows/` - Automated daily updates

## Local Usage

```bash
python generate_newsletter.py
# Open output/latest.html in browser
```

## Embedding in Patreon/Substack

1. Run the generator (or wait for daily auto-run)
2. Open `output/embed_snippet.html`
3. Copy the HTML content
4. Paste into your post editor (switch to HTML mode)

---

💖 For entertainment purposes only • Generated with love by Princess Upload
