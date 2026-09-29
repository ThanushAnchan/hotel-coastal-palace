@echo off
title Publish Hotel Coastal Palace to GitHub
cd /d "%~dp0"
echo ============================================================
echo Publishing Hotel Coastal Palace to GitHub...
echo Repository: https://github.com/ThanushAnchan/hotel-coastal-palace
echo ============================================================
git push -u origin main
echo ============================================================
echo If the upload succeeded, go to:
echo https://dashboard.render.com/select-repo?type=web
echo Select hotel-coastal-palace and click Deploy!
echo ============================================================
pause
