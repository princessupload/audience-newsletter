# Fix git rebase state
$rebasePath = ".git\rebase-merge"
if (Test-Path $rebasePath) {
    Remove-Item -Recurse -Force $rebasePath
    Write-Host "Removed rebase-merge"
}

# Remove other artifacts
@(".git\AUTO_MERGE", ".git\REBASE_HEAD", ".git\MERGE_MSG") | ForEach-Object {
    if (Test-Path $_) { Remove-Item -Force $_; Write-Host "Removed $_" }
}

# Reset to origin
git fetch origin
git reset --hard origin/master
Write-Host "Reset to origin/master"

# Show status
git status
