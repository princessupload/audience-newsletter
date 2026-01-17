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
        'method': 'email',  # Substack allows importing posts via email
        'import_email': os.environ.get('SUBSTACK_IMPORT_EMAIL', ''),  # Your Substack import email
        'description': 'Send newsletter HTML to Substack import email'
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
    """Publish to Substack via email import."""
    print("\n📧 Publishing to Substack...")
    
    import_email = CONFIG['substack']['import_email']
    if not import_email:
        print("   ⚠️  SUBSTACK_IMPORT_EMAIL not set")
        print("   📝 To enable Substack automation:")
        print("      1. Go to Substack Dashboard > Settings > Importing")
        print("      2. Get your unique import email address")
        print("      3. Set SUBSTACK_IMPORT_EMAIL environment variable")
        return False
    
    html = load_newsletter_html()
    if not html:
        print("   ❌ Newsletter HTML not found")
        return False
    
    subject = f"🎰 Lottery Newsletter - {datetime.now().strftime('%B %d, %Y')}"
    success, msg = send_email([import_email], subject, html, CONFIG['email'])
    
    if success:
        print(f"   ✅ Sent to Substack import: {import_email}")
    else:
        print(f"   ❌ {msg}")
    
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
