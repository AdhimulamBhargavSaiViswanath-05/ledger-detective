# Git Push Strategy & Secret Remediation Guide

## Issue Summary

GitHub detected a GCP API key in commit `8c9ee4ce` in file `PROGRESS.md:89`. This blocks all branch pushes.

**Commit Details**:
- **Commit**: 8c9ee4ce014d85cc3583297e6b663c7ffba7836e  
- **File**: PROGRESS.md (line 89)
- **Content**: API key was documented during Phase 3 troubleshooting
- **Current Status**: Key no longer in current files, but exists in git history

---

## Solution Options

### Option 1: Remove Secret from Git History (Recommended)

Use BFG Repo Cleaner to remove the secret from all commits:

\`\`\`bash
# 1. Backup your repository
cp -r ledger-detective ledger-detective-backup

# 2. Install BFG Repo Cleaner (if not installed)
# macOS:
brew install bfg

# 3. Create a file with the secret to remove
echo "[REDACTED_API_KEY]" > secrets.txt

# 4. Run BFG to remove the secret from history
cd ledger-detective
bfg --replace-text secrets.txt

# 5. Clean up and repack
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 6. Force push all branches (THIS REWRITES HISTORY!)
git push --force-with-lease --all origin
git push --force-with-lease --tags origin

# 7. Clean up
rm secrets.txt
\`\`\`

**⚠️ Warning**: This rewrites git history. All collaborators must re-clone the repository.

### Option 2: Use GitHub's Secret Bypass (Quick Fix)

GitHub provides a URL to allow the secret for this repository:

\`\`\`bash
# Visit this URL and click "Allow secret"
open "https://github.com/AdhimulamBhargavSaiViswanath-05/ledger-detective/security/secret-scanning/unblock-secret/3IG7Za6Ow5O9wJHPUqXmxPK7fLg"

# Then retry push
git push -u origin --all
\`\`\`

**Note**: This bypasses GitHub's protection but doesn't remove the secret from history.

### Option 3: Interactive Rebase (Manual, Most Control)

\`\`\`bash
# For each branch that contains the secret commit
git checkout feature/phase-3-sql-generation

# Start interactive rebase from before the problematic commit
git rebase -i 8c9ee4ce^

# In the editor, change 'pick' to 'edit' for commit 8c9ee4ce
# Save and exit

# Edit the file to remove the secret
nano PROGRESS.md  # Remove the API key line

# Amend the commit
git add PROGRESS.md
git commit --amend --no-edit

# Continue the rebase
git rebase --continue

# Repeat for all branches, then force push
git push --force-with-lease origin feature/phase-3-sql-generation
\`\`\`

---

## Current Branch Status

All branches contain the secret in commit `8c9ee4ce`:
- ✅ `main` - OK (hasn't been pushed yet)
- ❌ `dev` - Contains secret
- ❌ All `feature/phase-*` branches - Contain secret

---

## Recommended Workflow

### Step 1: Clean the Secret

Choose Option 1 (BFG) or Option 2 (GitHub bypass) above.

### Step 2: Push All Branches

\`\`\`bash
# Push main first (if clean)
git push -u origin main

# Push dev
git push -u origin dev

# Push all feature branches
git push -u origin --all
\`\`\`

### Step 3: Merge dev to main (via PR)

\`\`\`bash
# After branches are pushed, create PR on GitHub
gh pr create --base main --head dev --title "Merge dev to main - v1.0.0 Release" --body "
## Summary
Complete implementation of Ledger Detective - all 13 phases done!

## Changes
- ✅ 94 unit tests (100% passing)
- ✅ Mock LLM implementation
- ✅ Complete pipeline (Refusal → Ambiguity → SQL Gen → Validation → Execution → Composition)
- ✅ Streamlit UI
- ✅ Evaluation harness
- ✅ Comprehensive documentation

## Test Results
\`\`\`
94 passed, 2 warnings
\`\`\`

## Architecture
See ARCHITECTURE.md for complete system design with Mermaid diagrams.

## Ready for Production
Follow SWITCHING_TO_REAL_LLM.md to add API key and achieve ≥90% accuracy.
"

# Or create PR via GitHub web interface:
# https://github.com/AdhimulamBhargavSaiViswanath-05/ledger-detective/compare/main...dev
\`\`\`

### Step 4: Merge PR and Tag Release

\`\`\`bash
# After PR is approved and merged
git checkout main
git pull origin main

# Tag the release
git tag -a v1.0.0 -m "Ledger Detective v1.0.0 - Complete Implementation"
git push origin v1.0.0
\`\`\`

---

## Alternative: Fresh Start (If BFG is Complex)

If the above is too complex, you can create a clean repository:

\`\`\`bash
# 1. Create a new branch from current state
git checkout dev
git checkout -b clean-main

# 2. Remove git history
rm -rf .git
git init

# 3. Make initial commit with clean code
git add .
git commit -m "Ledger Detective v1.0.0 - Complete Implementation

- 94 unit tests (100% passing)
- Mock LLM implementation  
- Complete pipeline architecture
- Streamlit UI
- Comprehensive documentation
"

# 4. Add remote and push
git remote add origin git@github-personal:AdhimulamBhargavSaiViswanath-05/ledger-detective.git
git branch -M main
git push -u origin main --force
\`\`\`

**⚠️ Warning**: This loses all git history! Only use if you don't need the commit history.

---

## Current Documentation Status

All documentation is complete and committed to `dev`:

✅ **README.md** - User-facing documentation  
✅ **ARCHITECTURE.md** - Technical architecture with Mermaid diagrams  
✅ **PLAN.md** - Phase-by-phase implementation plan  
✅ **PROGRESS.md** - Development log  
✅ **SWITCHING_TO_REAL_LLM.md** - LLM integration guide  
✅ **HOW_TO_RUN.md** - Quick start guide  
✅ **ProblemSelection_Process.md** - Project rationale  

---

## Summary

1. **Secret Issue**: Old API key in git history blocks push
2. **Solution**: Use BFG Repo Cleaner or GitHub's bypass option
3. **After Fix**: Push all branches with `git push --all`
4. **Final Step**: Create PR from `dev` to `main` and merge

**Status**: Ready to proceed once secret is removed from history.
