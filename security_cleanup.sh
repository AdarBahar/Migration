#!/bin/bash
#
# 🔒 Security Cleanup Script
# Removes sensitive data from files and git history
#
# Usage: ./security_cleanup.sh
#
# WARNING: This script will rewrite git history!
# Make sure you have a backup before running this script.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔒 Security Cleanup Script${NC}"
echo -e "${BLUE}===========================${NC}"
echo ""

# Step 1: Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  WARNING: This script will:${NC}"
echo -e "${YELLOW}   1. Remove hardcoded passwords from files${NC}"
echo -e "${YELLOW}   2. Rewrite git history to remove sensitive data${NC}"
echo -e "${YELLOW}   3. Force push to remote (if confirmed)${NC}"
echo ""
echo -e "${YELLOW}   Make sure you have a backup!${NC}"
echo ""

read -p "Do you want to continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo -e "${RED}❌ Aborted${NC}"
    exit 0
fi

# Step 2: Create backup
echo ""
echo -e "${BLUE}📦 Creating backup...${NC}"
BACKUP_DIR="../Migration-backup-$(date +%Y%m%d-%H%M%S)"
cp -r . "$BACKUP_DIR"
echo -e "${GREEN}✅ Backup created at: $BACKUP_DIR${NC}"

# Step 3: Fix current files
echo ""
echo -e "${BLUE}🔧 Fixing current files...${NC}"

# Fix test_migration_center.py
if [ -f "test_migration_center.py" ]; then
    echo "   Fixing test_migration_center.py..."
    sed -i.bak 's/REDIS_DEST_PASSWORD=testpass/REDIS_DEST_PASSWORD=PLACEHOLDER_PASSWORD/g' test_migration_center.py
    rm -f test_migration_center.py.bak
    echo -e "${GREEN}   ✅ Fixed test_migration_center.py${NC}"
fi

# Fix test_env_update.py
if [ -f "test_env_update.py" ]; then
    echo "   Fixing test_env_update.py..."
    sed -i.bak 's/REDIS_DEST_PASSWORD=mypassword/REDIS_DEST_PASSWORD=PLACEHOLDER_PASSWORD/g' test_env_update.py
    rm -f test_env_update.py.bak
    echo -e "${GREEN}   ✅ Fixed test_env_update.py${NC}"
fi

# Fix manage_env.py - make examples more obvious
if [ -f "manage_env.py" ]; then
    echo "   Fixing manage_env.py..."
    sed -i.bak 's/mypassword/EXAMPLE_PASSWORD/g' manage_env.py
    sed -i.bak 's/pass123/EXAMPLE_PASSWORD/g' manage_env.py
    sed -i.bak 's/:secret@/:EXAMPLE_PASSWORD@/g' manage_env.py
    rm -f manage_env.py.bak
    echo -e "${GREEN}   ✅ Fixed manage_env.py${NC}"
fi

# Step 4: Commit fixes
echo ""
echo -e "${BLUE}💾 Committing fixes...${NC}"
git add test_migration_center.py test_env_update.py manage_env.py 2>/dev/null || true
git commit -m "🔒 Security: Remove hardcoded passwords from test files" || echo "No changes to commit"

# Step 5: Create passwords.txt for BFG
echo ""
echo -e "${BLUE}📝 Creating passwords.txt for BFG...${NC}"
cat > passwords.txt << 'EOF'
testpass==>REDACTED_PASSWORD
mypassword==>REDACTED_PASSWORD
pass123==>EXAMPLE_PASSWORD
secret==>EXAMPLE_PASSWORD
EOF
echo -e "${GREEN}✅ Created passwords.txt${NC}"

# Step 6: Check if BFG is installed
echo ""
echo -e "${BLUE}🔍 Checking for BFG Repo-Cleaner...${NC}"
if ! command -v bfg &> /dev/null; then
    echo -e "${YELLOW}⚠️  BFG Repo-Cleaner not found${NC}"
    echo ""
    echo "To install BFG:"
    echo "  macOS:   brew install bfg"
    echo "  Linux:   Download from https://rtyley.github.io/bfg-repo-cleaner/"
    echo "  Windows: Download JAR from https://rtyley.github.io/bfg-repo-cleaner/"
    echo ""
    echo "After installing, run this script again or manually run:"
    echo "  bfg --replace-text passwords.txt"
    echo "  git reflog expire --expire=now --all"
    echo "  git gc --prune=now --aggressive"
    exit 0
fi

# Step 7: Run BFG
echo ""
echo -e "${YELLOW}⚠️  About to clean git history with BFG${NC}"
read -p "Continue with BFG cleanup? (yes/no): " bfg_confirm
if [ "$bfg_confirm" != "yes" ]; then
    echo -e "${YELLOW}⚠️  Skipping BFG cleanup${NC}"
    echo "You can run it manually later with:"
    echo "  bfg --replace-text passwords.txt"
    exit 0
fi

echo -e "${BLUE}🧹 Running BFG Repo-Cleaner...${NC}"
bfg --replace-text passwords.txt

# Step 8: Clean up git
echo ""
echo -e "${BLUE}🧹 Cleaning up git repository...${NC}"
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo -e "${GREEN}✅ Git repository cleaned${NC}"

# Step 9: Ask about force push
echo ""
echo -e "${YELLOW}⚠️  Git history has been rewritten${NC}"
echo -e "${YELLOW}   All team members will need to re-clone the repository${NC}"
echo ""
read -p "Force push to remote? (yes/no): " push_confirm
if [ "$push_confirm" == "yes" ]; then
    echo -e "${BLUE}🚀 Force pushing to remote...${NC}"
    git push origin --force --all
    git push origin --force --tags
    echo -e "${GREEN}✅ Pushed to remote${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT: Notify all team members to:${NC}"
    echo -e "${YELLOW}   1. Delete their local repository${NC}"
    echo -e "${YELLOW}   2. Re-clone from GitHub${NC}"
    echo -e "${YELLOW}   3. Update their .env files with new credentials${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping push to remote${NC}"
    echo "You can push manually later with:"
    echo "  git push origin --force --all"
    echo "  git push origin --force --tags"
fi

# Step 10: Cleanup
echo ""
echo -e "${BLUE}🧹 Cleaning up temporary files...${NC}"
rm -f passwords.txt
echo -e "${GREEN}✅ Cleanup complete${NC}"

# Step 11: Summary
echo ""
echo -e "${GREEN}✅ Security cleanup completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "  1. Rotate all Redis Cloud passwords"
echo "  2. Update .env files with new credentials"
echo "  3. Verify no secrets remain: git log --all -S 'password'"
echo "  4. Install pre-commit hooks (see SECURITY_CLEANUP.md)"
echo "  5. Enable GitHub secret scanning"
echo ""
echo -e "${BLUE}📁 Backup location: $BACKUP_DIR${NC}"
echo ""

