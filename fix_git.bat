@echo off
cd /d "c:\Users\Slytherin\CascadeProjects\windsurf-project-3\lottery-audience-newsletter"
git rebase --abort 2>nul
git fetch origin
git reset --hard origin/master
echo Git reset complete!
