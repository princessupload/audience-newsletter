"""Fix git state and push LA fix to GitHub."""
import subprocess
import shutil
import os

os.chdir(r'c:\Users\Slytherin\CascadeProjects\windsurf-project-3\lottery-audience-newsletter')

# Step 1: Clean up rebase state
rebase_path = '.git/rebase-merge'
if os.path.exists(rebase_path):
    shutil.rmtree(rebase_path)
    print("1. Cleaned rebase-merge state")
else:
    print("1. No rebase state to clean")

# Clean other merge artifacts
for f in ['.git/AUTO_MERGE', '.git/MERGE_MSG', '.git/REBASE_HEAD']:
    if os.path.exists(f):
        os.remove(f)
        print(f"   Removed {f}")

# Step 2: Reset to origin/master
print("\n2. Resetting to origin/master...")
result = subprocess.run(['git', 'reset', '--hard', 'origin/master'], capture_output=True, text=True)
print(result.stdout or result.stderr)

# Step 3: Check current status
print("\n3. Current status:")
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
print(result.stdout or "Clean")

# Step 4: Show recent commits from origin
print("\n4. Recent commits on origin/master:")
result = subprocess.run(['git', 'log', 'origin/master', '-3', '--oneline'], capture_output=True, text=True)
print(result.stdout)

print("\n✅ Git state fixed! The LA fix needs to be re-applied to update_data.py")
