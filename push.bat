@echo off
cd /d "D:\Upwork Sniper"
echo Pulling latest changes from GitHub...
git pull origin main --rebase
echo.
echo Adding all files...
git add .
echo.
echo Committing...
git commit -m "Update: All fixes - config duplicates, profile context, conflict markers"
echo.
echo Pushing to GitHub...
git push origin main
echo.
echo Done! Check GitHub: https://github.com/babyfox1306/Upwork-AI-Assistant
pause

