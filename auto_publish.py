"""
Full auto-publish pipeline for lottery newsletter.
1. Updates lottery data
2. Generates fresh newsletter
3. Uploads to princessupload.net
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent

def run_script(script_name):
    """Run a Python script and return success status."""
    script_path = BASE_DIR / script_name
    if not script_path.exists():
        print(f"   ❌ Script not found: {script_name}")
        return False
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(BASE_DIR),
        capture_output=False
    )
    return result.returncode == 0

def main():
    print("=" * 60)
    print(f"🎰 LOTTERY NEWSLETTER AUTO-PUBLISH")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Update data
    print("\n📊 Step 1: Updating lottery data...")
    run_script("update_data.py")
    
    # Step 2: Generate newsletter
    print("\n📝 Step 2: Generating newsletter...")
    run_script("generate_newsletter.py")
    
    # Step 3: Upload to WordPress
    print("\n🚀 Step 3: Uploading to princessupload.net...")
    run_script("upload_to_wordpress.py")
    
    print("\n" + "=" * 60)
    print("✅ AUTO-PUBLISH COMPLETE!")
    print("🌐 https://www.princessupload.net/lottery-newsletter.html")
    print("=" * 60)

if __name__ == "__main__":
    main()
