"""
Upload newsletter to WordPress via SFTP.
Auto-uploads latest.html to princessupload.net
"""

import os
import paramiko
from pathlib import Path
from datetime import datetime

# SFTP Configuration
SFTP_HOST = "iad1-shared-b8-12.dreamhost.com"
SFTP_USER = "societyofsara"
SFTP_PASS = os.environ.get("SFTP_PASSWORD", "8020ruler@")

# Paths
LOCAL_FILE = Path(__file__).parent / "output" / "latest.html"
REMOTE_DIR = "/home/societyofsara/princessupload.net"  # Adjust if different
REMOTE_FILE = "lottery-newsletter.html"

def upload_newsletter():
    """Upload the newsletter via SFTP."""
    print(f"\n🚀 Uploading newsletter to princessupload.net...")
    print(f"   Local: {LOCAL_FILE}")
    
    if not LOCAL_FILE.exists():
        print("   ❌ latest.html not found! Run generate_newsletter.py first.")
        return False
    
    try:
        # Connect via SFTP
        print(f"   Connecting to {SFTP_HOST}...")
        transport = paramiko.Transport((SFTP_HOST, 22))
        transport.connect(username=SFTP_USER, password=SFTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # List directories to find the right path
        print("   Finding website directory...")
        try:
            dirs = sftp.listdir("/home/societyofsara")
            print(f"   Available dirs: {dirs}")
        except:
            pass
        
        # Try common WordPress paths
        possible_paths = [
            "/home/societyofsara/princessupload.net",
            "/home/societyofsara/www",
            "/home/societyofsara/public_html",
            "/princessupload.net",
        ]
        
        remote_path = None
        for path in possible_paths:
            try:
                sftp.stat(path)
                remote_path = path
                print(f"   ✅ Found: {path}")
                break
            except:
                continue
        
        if not remote_path:
            # List root to see what's available
            try:
                root_dirs = sftp.listdir("/home/societyofsara")
                print(f"   Available in /home/societyofsara: {root_dirs}")
                # Use first directory that looks like a website
                for d in root_dirs:
                    if 'princess' in d.lower() or 'www' in d.lower() or 'public' in d.lower():
                        remote_path = f"/home/societyofsara/{d}"
                        break
                if not remote_path and root_dirs:
                    remote_path = f"/home/societyofsara/{root_dirs[0]}"
            except Exception as e:
                print(f"   Error listing: {e}")
                remote_path = "/home/societyofsara"
        
        # Upload the file
        remote_file_path = f"{remote_path}/{REMOTE_FILE}"
        print(f"   Uploading to: {remote_file_path}")
        sftp.put(str(LOCAL_FILE), remote_file_path)
        
        print(f"   ✅ Upload complete!")
        print(f"   🌐 View at: https://www.princessupload.net/{REMOTE_FILE}")
        
        sftp.close()
        transport.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        return False

if __name__ == "__main__":
    upload_newsletter()
