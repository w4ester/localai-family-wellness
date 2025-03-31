#!/bin/bash

# Change to the project directory
cd /Users/willf/smartIndex/epicforesters/localai-family-wellness

# Remove files from git tracking but keep them locally
git rm --cached .env.local
git rm --cached .env.txt
git rm --cached .env.l.bak
git rm --cached .env

# Commit the changes
git add .gitignore
git commit -m "Improved environment file handling and security"

echo "Successfully removed env files from git tracking while keeping them locally"
echo "Run 'git push origin main' to push these changes to GitHub"
