import shutil
import os
import subprocess

# Clean up rebase state
rebase_path = '.git/rebase-merge'
if os.path.exists(rebase_path):
    shutil.rmtree(rebase_path)
    print("Cleaned rebase state")

# Also clean AUTO_MERGE if exists
auto_merge = '.git/AUTO_MERGE'
if os.path.exists(auto_merge):
    os.remove(auto_merge)
    print("Cleaned AUTO_MERGE")

# Reset to origin/master
result = subprocess.run(['git', 'reset', '--hard', 'origin/master'], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)
print("Done!")
