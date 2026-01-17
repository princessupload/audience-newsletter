#!/usr/bin/env python3
"""
Automated Newsletter Sender
Fetches subscribers from website and sends newsletter to all of them.
Includes unsubscribe link in every email.

Run via GitHub Actions daily at noon CT.
"""

import os
import json
import smtplib
import hashlib
import urllib.request
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / 'output'
LOCAL_SUBSCRIBERS = BASE_DIR / 'subscribers.txt'
LOCAL_UNSUBSCRIBED = BASE_DIR / 'unsubscribed.txt'

# Website subscriber endpoint
SUBSCRIBER_API = "https://www.princessupload.net/subscribe.php"

# Email configuration (from environment variables only - no hardcoded secrets)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get('GMAIL_USER', '')
SENDER_PASSWORD = os.environ.get('GMAIL_PASSWORD', '')

def get_unsub_token(email):
    """Generate unsubscribe token for email."""
    return hashlib.md5((email + 'lottery_unsub_2026').encode()).hexdigest()[:16]

def get_unsub_link(email):
    """Generate full unsubscribe link."""
    token = get_unsub_token(email)
    return f"https://www.princessupload.net/subscribe.php?email={email}&token={token}"

def load_local_subscribers():
    """Load subscribers from local file."""
    subscribers = set()
    if LOCAL_SUBSCRIBERS.exists():
        with open(LOCAL_SUBSCRIBERS, 'r') as f:
            for line in f:
                email = line.strip().lower()
                if email and '@' in email and not email.startswith('#'):
                    subscribers.add(email)
    return subscribers

def load_local_unsubscribed():
    """Load unsubscribed emails from local file."""
    unsubscribed = set()
    if LOCAL_UNSUBSCRIBED.exists():
        with open(LOCAL_UNSUBSCRIBED, 'r') as f:
            for line in f:
                email = line.strip().lower()
                if email and '@' in email:
                    unsubscribed.add(email)
    return unsubscribed

def fetch_website_subscribers():
    """Fetch subscriber list from website (if available)."""
    try:
        # Try to fetch from website API
        req = urllib.request.Request(
            f"{SUBSCRIBER_API}?action=list&key={os.environ.get('SUBSCRIBER_KEY', '')}",
            headers={'User-Agent': 'LotteryNewsletter/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get('success') and data.get('subscribers'):
                return set(data['subscribers'])
    except Exception as e:
        print(f"   Could not fetch from website: {e}")
    return set()

def get_all_subscribers():
    """Get combined subscriber list from all sources."""
    # Get local subscribers
    local = load_local_subscribers()
    print(f"   Local subscribers: {len(local)}")
    
    # Get website subscribers  
    website = fetch_website_subscribers()
    print(f"   Website subscribers: {len(website)}")
    
    # Combine
    all_subs = local | website
    
    # Remove unsubscribed
    unsubscribed = load_local_unsubscribed()
    print(f"   Unsubscribed: {len(unsubscribed)}")
    
    active = all_subs - unsubscribed
    print(f"   Active subscribers: {len(active)}")
    
    return active

def load_newsletter():
    """Load latest newsletter HTML."""
    newsletter_file = OUTPUT_DIR / 'latest.html'
    if not newsletter_file.exists():
        return None, None
    
    with open(newsletter_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Extract title from HTML
    import re
    title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
    title = title_match.group(1) if title_match else f"Lottery Newsletter - {datetime.now().strftime('%B %d, %Y')}"
    
    return html, title

def inject_unsubscribe_link(html, email):
    """Inject personalized unsubscribe link into newsletter."""
    unsub_link = get_unsub_link(email)
    
    # Replace the generic unsubscribe section
    old_unsub = 'To unsubscribe, reply to this email with "UNSUBSCRIBE" in the subject line.'
    new_unsub = f'<a href="{unsub_link}" style="color: #888;">Click here to unsubscribe</a> or reply with "UNSUBSCRIBE".'
    
    html = html.replace(old_unsub, new_unsub)
    
    # Also add unsubscribe header-compatible link at bottom
    if '</body>' in html:
        footer = f'''
        <div style="text-align: center; padding: 20px; font-size: 12px; color: #999;">
            <a href="{unsub_link}" style="color: #999;">Unsubscribe</a> from this newsletter
        </div>
        </body>'''
        html = html.replace('</body>', footer)
    
    return html

def send_newsletter(email, html, subject):
    """Send newsletter to a single subscriber."""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print(f"   ⚠️ Email credentials not configured")
        return False
    
    try:
        # Personalize the newsletter with unsubscribe link
        personalized_html = inject_unsubscribe_link(html, email)
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f"Princess Upload <{SENDER_EMAIL}>"
        msg['To'] = email
        msg['Subject'] = subject
        msg['List-Unsubscribe'] = f"<{get_unsub_link(email)}>"
        msg['List-Unsubscribe-Post'] = "List-Unsubscribe=One-Click"
        
        # HTML version
        msg.attach(MIMEText(personalized_html, 'html', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
        
        return True
    except Exception as e:
        print(f"   ❌ Failed to send to {email}: {e}")
        return False

def main():
    """Main function to send newsletter to all subscribers."""
    print(f"\n{'='*60}")
    print(f"📧 NEWSLETTER SENDER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Load newsletter
    print("📄 Loading newsletter...")
    html, subject = load_newsletter()
    if not html:
        print("   ❌ No newsletter found! Run generate_newsletter.py first.")
        return
    print(f"   ✅ Loaded: {subject}")
    
    # Get subscribers
    print("\n👥 Loading subscribers...")
    subscribers = get_all_subscribers()
    
    if not subscribers:
        print("   ⚠️ No subscribers found")
        return
    
    # Send to each subscriber
    print(f"\n📤 Sending to {len(subscribers)} subscribers...")
    success = 0
    failed = 0
    
    for email in sorted(subscribers):
        result = send_newsletter(email, html, subject)
        if result:
            success += 1
            print(f"   ✅ {email}")
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"📊 RESULTS: {success} sent, {failed} failed")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
