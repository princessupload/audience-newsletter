#!/usr/bin/env python3
"""
Newsletter Publishing Automation
Supports: Substack (via email), Patreon (via API), Direct Email

Usage:
    python publish_newsletter.py --all          # Publish to all platforms
    python publish_newsletter.py --substack     # Email to Substack import
    python publish_newsletter.py --patreon      # Post to Patreon (requires API key)
    python publish_newsletter.py --email        # Send to email list
"""

import os
import json
import smtplib
import argparse
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / 'output'

# Configuration
CONFIG = {
    'substack': {
        'enabled': True,
        'method': 'post_email',  # Email to Substack's post address = auto-publish to all subscribers
        'post_email': os.environ.get('SUBSTACK_POST_EMAIL', ''),  # yourname+post@mg.substack.com
        'description': 'Email to Substack post address = auto-sends to ALL subscribers'
    },
    'patreon': {
        'enabled': True,
        'method': 'api',  # Patreon has an API for posting
        'api_key': os.environ.get('PATREON_API_KEY', ''),
        'campaign_id': os.environ.get('PATREON_CAMPAIGN_ID', ''),
        'description': 'Post to Patreon via API (requires creator access token)'
    },
    'email': {
        'enabled': True,
        'recipients': [
            'sarasinead@aol.com',
            'marysineadart@gmail.com',
            'princessuploadie@gmail.com',
            'rick@gamingdatasystems.com'
        ],
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': os.environ.get('GMAIL_USER', 'princessuploadie@gmail.com'),
        'sender_password': os.environ.get('GMAIL_PASSWORD', '')
    }
}

def load_subscribers():
    """Load subscriber emails from file, excluding unsubscribed."""
    subscribers_file = BASE_DIR / 'subscribers.txt'
    unsubscribed_file = BASE_DIR / 'unsubscribed.txt'
    
    # Load unsubscribed emails
    unsubscribed = set()
    if unsubscribed_file.exists():
        with open(unsubscribed_file, 'r') as f:
            for line in f:
                email = line.strip().lower()
                if email and '@' in email:
                    unsubscribed.add(email)
    
    if not subscribers_file.exists():
        return []
    
    subscribers = []
    with open(subscribers_file, 'r') as f:
        for line in f:
            email = line.strip()
            if email and '@' in email and not email.startswith('#'):
                # Skip unsubscribed emails
                if email.lower() not in unsubscribed:
                    subscribers.append(email)
    return subscribers

def add_unsubscribe(email):
    """Add email to unsubscribed list."""
    unsubscribed_file = BASE_DIR / 'unsubscribed.txt'
    email = email.strip().lower()
    
    # Check if already unsubscribed
    existing = set()
    if unsubscribed_file.exists():
        with open(unsubscribed_file, 'r') as f:
            existing = {line.strip().lower() for line in f if line.strip()}
    
    if email not in existing:
        with open(unsubscribed_file, 'a') as f:
            f.write(f"{email}\n")
        print(f"   ✅ Unsubscribed: {email}")
        return True
    return False

def sync_substack_subscribers():
    """
    NOTE: Substack does NOT have a public API for fetching subscribers.
    You must manually export subscribers from Substack Dashboard.
    
    Steps:
    1. Go to Substack > Subscribers
    2. Click Export (top right)
    3. Download CSV
    4. Copy email addresses to subscribers.txt
    
    This function checks if subscribers.txt was recently updated.
    """
    subscribers_file = BASE_DIR / 'subscribers.txt'
    
    if not subscribers_file.exists():
        print("   ⚠️  No subscribers.txt found")
        print("   📝 Export your Substack subscribers manually:")
        print("      1. Substack > Subscribers > Export")
        print("      2. Copy emails to subscribers.txt")
        return False
    
    # Check file modification time
    import os
    mtime = os.path.getmtime(subscribers_file)
    last_modified = datetime.fromtimestamp(mtime)
    days_old = (datetime.now() - last_modified).days
    
    if days_old > 7:
        print(f"   ⚠️  subscribers.txt is {days_old} days old!")
        print("   📝 Consider re-exporting from Substack for new subscribers")
    else:
        print(f"   ✅ subscribers.txt updated {days_old} days ago")
    
    return True

def load_newsletter_html():
    """Load the latest newsletter HTML."""
    latest_path = OUTPUT_DIR / 'latest.html'
    if latest_path.exists():
        return latest_path.read_text(encoding='utf-8')
    return None

def load_embed_snippet():
    """Load the embed snippet (simplified HTML for platforms)."""
    embed_path = OUTPUT_DIR / 'embed_snippet.html'
    if embed_path.exists():
        return embed_path.read_text(encoding='utf-8')
    return None

def send_email(to_addresses, subject, html_content, config):
    """Send HTML email."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = config['sender_email']
        msg['To'] = ', '.join(to_addresses) if isinstance(to_addresses, list) else to_addresses
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.sendmail(config['sender_email'], to_addresses, msg.as_string())
        
        return True, "Email sent successfully"
    except Exception as e:
        return False, f"Email error: {e}"

def publish_to_substack():
    """Publish to Substack via post-by-email (auto-sends to ALL subscribers)."""
    print("\n📧 Publishing to Substack...")
    
    post_email = CONFIG['substack']['post_email']
    if not post_email:
        print("   ⚠️  SUBSTACK_POST_EMAIL not configured!")
        print("")
        print("   📝 ONE-TIME SETUP (do this now):")
        print("      1. Go to Substack → Settings → Publishing")
        print("      2. Enable 'Post via email'")
        print("      3. Copy your posting email (looks like: yourname+post@mg.substack.com)")
        print("      4. Run this command in PowerShell:")
        print("")
        print('      [Environment]::SetEnvironmentVariable("SUBSTACK_POST_EMAIL", "YOUR_EMAIL_HERE", "User")')
        print("")
        print("      5. Restart your terminal and run again!")
        return False
    
    html = load_newsletter_html()
    if not html:
        print("   ❌ Newsletter HTML not found")
        return False
    
    subject = f"🎰 Lottery Pool Picks - {datetime.now().strftime('%B %d, %Y')}"
    
    # Send to Substack's post email - this auto-publishes to ALL subscribers!
    success, msg = send_email([post_email], subject, html, CONFIG['email'])
    
    if success:
        print(f"   ✅ Sent to Substack! Auto-publishing to all subscribers...")
        print(f"   📬 Check your Substack dashboard to confirm")
    else:
        print(f"   ❌ Failed: {msg}")
    
    return success

def publish_to_patreon():
    """Publish to Patreon via API."""
    print("\n🎨 Publishing to Patreon...")
    
    api_key = CONFIG['patreon']['api_key']
    campaign_id = CONFIG['patreon']['campaign_id']
    
    if not api_key or not campaign_id:
        print("   ⚠️  Patreon API not configured")
        print("   📝 To enable Patreon automation:")
        print("      1. Go to Patreon > My Creator Page > Settings > Developers")
        print("      2. Create a new API client and get access token")
        print("      3. Set PATREON_API_KEY and PATREON_CAMPAIGN_ID environment variables")
        print("   📋 Manual option: Copy embed_snippet.html content into a Patreon post")
        return False
    
    try:
        import urllib.request
        
        html = load_embed_snippet() or load_newsletter_html()
        if not html:
            print("   ❌ Newsletter HTML not found")
            return False
        
        # Patreon API endpoint for creating posts
        url = "https://www.patreon.com/api/oauth2/v2/campaigns/{}/posts".format(campaign_id)
        
        post_data = {
            "data": {
                "type": "post",
                "attributes": {
                    "title": f"🎰 Lottery Newsletter - {datetime.now().strftime('%B %d, %Y')}",
                    "content": html,
                    "is_public": False,  # Patrons only
                    "post_type": "text_only"
                }
            }
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(post_data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as resp:
            if resp.status == 201:
                print("   ✅ Posted to Patreon successfully!")
                return True
            else:
                print(f"   ❌ Patreon API returned status {resp.status}")
                return False
                
    except Exception as e:
        print(f"   ❌ Patreon API error: {e}")
        return False

def publish_to_email():
    """Send newsletter to email list."""
    print("\n📬 Sending to email list...")
    
    recipients = CONFIG['email']['recipients']
    if not recipients:
        print("   ⚠️  No email recipients configured")
        return False
    
    html = load_newsletter_html()
    if not html:
        print("   ❌ Newsletter HTML not found")
        return False
    
    subject = f"🎰 Lottery Newsletter - {datetime.now().strftime('%B %d, %Y')}"
    success, msg = send_email(recipients, subject, html, CONFIG['email'])
    
    if success:
        print(f"   ✅ Sent to {len(recipients)} recipients")
    else:
        print(f"   ❌ {msg}")
    
    return success

def main():
    parser = argparse.ArgumentParser(description='Publish lottery newsletter to various platforms')
    parser.add_argument('--all', action='store_true', help='Publish to all platforms')
    parser.add_argument('--substack', action='store_true', help='Publish to Substack')
    parser.add_argument('--patreon', action='store_true', help='Publish to Patreon')
    parser.add_argument('--email', action='store_true', help='Send to email list')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without publishing')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("📰 NEWSLETTER PUBLISHER")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    if args.dry_run:
        print("\n🔍 DRY RUN - No actual publishing will occur\n")
        print("Available platforms:")
        for platform, config in CONFIG.items():
            status = "✅ Configured" if config.get('enabled') else "❌ Not configured"
            print(f"  - {platform}: {status}")
        return
    
    results = {}
    
    if args.all or args.substack:
        results['substack'] = publish_to_substack()
    
    if args.all or args.patreon:
        results['patreon'] = publish_to_patreon()
    
    if args.all or args.email:
        results['email'] = publish_to_email()
    
    if not any([args.all, args.substack, args.patreon, args.email]):
        print("\n⚠️  No platform specified. Use --help for options.")
        print("\nQuick start:")
        print("  python publish_newsletter.py --email      # Send to family")
        print("  python publish_newsletter.py --all        # Publish everywhere")
    
    print("\n" + "=" * 50)
    print("📊 RESULTS")
    print("=" * 50)
    for platform, success in results.items():
        status = "✅ Success" if success else "❌ Failed/Skipped"
        print(f"  {platform}: {status}")

if __name__ == '__main__':
    main()
