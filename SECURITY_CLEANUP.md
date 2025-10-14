# 🔒 Security Cleanup Guide

## ⚠️ Security Issues Found

The following files contain hardcoded credentials or sensitive information:

### 1. **test_migration_center.py** (Line 40)
```python
REDIS_DEST_PASSWORD=testpass
```
**Issue**: Hardcoded test password in test file

### 2. **test_env_update.py** (Line 28)
```python
REDIS_DEST_PASSWORD=mypassword
```
**Issue**: Hardcoded test password in test file

### 3. **manage_env.py** (Lines 1240-1242)
```python
redis_samples = [
    "redis://default:mypassword@redis-xxxxx.c123.region-1.ec2.redns.redis-cloud.com:12345",
    "rediss://user:pass123@redis-yyyyy.c456.region-2.ec2.redns.redis-cloud.com:15000",
    "redis-cli -u redis://default:secret@redis-zzzzz.c789.region-3.ec2.redns.redis-cloud.com:16000"
]
```
**Issue**: Example passwords in test code (though these are fake examples)

---

## 🛡️ Cleanup Actions Required

### Step 1: Remove Sensitive Data from Current Files

1. **test_migration_center.py** - Replace hardcoded password with placeholder
2. **test_env_update.py** - Replace hardcoded password with placeholder
3. **manage_env.py** - Already using fake examples, but make it more obvious

### Step 2: Clean Git History

Use BFG Repo-Cleaner or git-filter-repo to remove sensitive data from history:

```bash
# Option 1: Using BFG Repo-Cleaner (recommended)
# Install: brew install bfg (macOS) or download from https://rtyley.github.io/bfg-repo-cleaner/

# Create a backup first!
cd ..
cp -r Migration Migration-backup

# Clean passwords from history
cd Migration
bfg --replace-text passwords.txt

# Force push (WARNING: This rewrites history!)
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin --force --all
git push origin --force --tags

# Option 2: Using git-filter-repo (more powerful)
# Install: pip install git-filter-repo

git filter-repo --replace-text passwords.txt
git push origin --force --all
git push origin --force --tags
```

### Step 3: Create passwords.txt for BFG

Create a file called `passwords.txt` with patterns to replace:

```
testpass==>REDACTED_PASSWORD
mypassword==>REDACTED_PASSWORD
pass123==>EXAMPLE_PASSWORD
secret==>EXAMPLE_PASSWORD
```

### Step 4: Rotate All Credentials

After cleaning the repository:

1. **Change all Redis Cloud passwords**
2. **Rotate AWS credentials** (if any were exposed)
3. **Update .env files** with new credentials
4. **Verify no credentials in .env are committed**

---

## 🔐 Prevention Measures

### 1. Add .gitignore Rules

Ensure `.gitignore` contains:

```gitignore
# Environment files
.env
.env.*
!.env.example

# Credentials
*password*
*secret*
*credentials*

# AWS
*.pem
*.key

# Test files with credentials
test_*.env
```

### 2. Use Environment Variables

**Never hardcode credentials**. Always use:

```python
import os
from dotenv import load_dotenv

load_dotenv()

password = os.getenv('REDIS_PASSWORD')  # ✅ Good
password = "mypassword"                  # ❌ Bad
```

### 3. Use Example/Template Files

Create `.env.example` with placeholders:

```bash
# .env.example
REDIS_SOURCE_HOST=your-redis-host.com
REDIS_SOURCE_PORT=6379
REDIS_SOURCE_PASSWORD=your-password-here
```

### 4. Pre-commit Hooks

Install git-secrets or similar tools:

```bash
# Install git-secrets
brew install git-secrets  # macOS
# or
git clone https://github.com/awslabs/git-secrets.git
cd git-secrets
make install

# Setup in repository
cd /path/to/Migration
git secrets --install
git secrets --register-aws
git secrets --add 'password\s*=\s*["\'][^"\']+["\']'
git secrets --add 'redis://[^@]+:[^@]+@'
```

### 5. GitHub Secret Scanning

Enable GitHub's secret scanning:

1. Go to repository Settings
2. Security & analysis
3. Enable "Secret scanning"
4. Enable "Push protection"

---

## 📋 Cleanup Checklist

- [ ] Backup repository
- [ ] Remove hardcoded passwords from current files
- [ ] Create passwords.txt for BFG
- [ ] Run BFG Repo-Cleaner
- [ ] Force push cleaned history
- [ ] Rotate all exposed credentials
- [ ] Update .gitignore
- [ ] Create .env.example
- [ ] Install pre-commit hooks
- [ ] Enable GitHub secret scanning
- [ ] Verify no secrets in repository
- [ ] Document security practices in README

---

## 🚨 Emergency Response

If credentials are already exposed:

1. **Immediately rotate all credentials**
2. **Check access logs** for unauthorized access
3. **Run security scan** on affected systems
4. **Clean git history** as described above
5. **Force push** to overwrite history
6. **Notify team members** to re-clone repository
7. **Document incident** for future reference

---

## 📚 Additional Resources

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [git-filter-repo](https://github.com/newren/git-filter-repo)
- [git-secrets](https://github.com/awslabs/git-secrets)
- [AWS: Best practices for managing credentials](https://docs.aws.amazon.com/general/latest/gr/aws-access-keys-best-practices.html)

---

## ✅ Verification

After cleanup, verify no secrets remain:

```bash
# Search for potential secrets
git log --all --source --full-history -S "password" --pretty=format:"%H %s"
git log --all --source --full-history -S "redis://" --pretty=format:"%H %s"

# Use truffleHog to scan for secrets
pip install trufflehog
trufflehog filesystem . --only-verified

# Use gitleaks
brew install gitleaks
gitleaks detect --source . --verbose
```

