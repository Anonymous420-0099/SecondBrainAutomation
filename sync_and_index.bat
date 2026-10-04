@echo off
echo ========================================================
echo   Second Brain: Syncing with GitHub & Re-indexing
echo ========================================================
git pull origin main
python build_system.py
echo ========================================================
echo   Sync & Re-index Complete!
echo ========================================================
