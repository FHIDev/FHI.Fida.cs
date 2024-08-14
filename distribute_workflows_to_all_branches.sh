# Get a list of all branches
branches=$(git branch -r | grep -v '\->' | grep -v 'main' | sed 's/origin\///')

for branch in $branches; do
  echo "Processing branch: $branch"
  
  # Checkout the branch
  git checkout $branch
  
  # Merge the .github directory from main
  git checkout main -- .github
  
  # Add, commit, and push the changes
  git add .github
  git commit -m "Update .github directory from main"
  git push origin $branch
done

# Checkout main branch again
git checkout main