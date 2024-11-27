#!/bin/bash

# Directory to save (replace with your directory path)
directory_to_save="./*.py"

# Remote repository URL (replace with your actual URL)
remote_url="git@github.com:phisan-chula/InundatCoast.git"

# Initialize a Git repository in the directory (if not already done)
if [ ! -d "$directory_to_save/.git" ]; then
  git init "$directory_to_save"
fi

# Add all files in the directory
git add -A "$directory_to_save"

# Commit the changes with a message (replace with your message)
git commit -m "Saving directory to GitHub"

# Add the remote repository
git remote add origin "$remote_url"

# Push the changes to the remote repository
git push -u origin main

echo "Directory saved to GitHub!"

