# GitHub Setup — WiFi AC Guardian

Configuration reference for connecting this repository to its remote GitHub origin.

---

## Repository Information

**Repository URL**:  
```
<REPOSITORY_URL_PLACEHOLDER>
```

Example format: `https://github.com/username/wifi-ac-guardian.git`

**Remote Name**: `origin`

**Default Branch**: `main`

---

## Authentication

This repository uses a GitHub Personal Access Token (PAT) for authentication.

**Token Type**: Fine-grained personal access token  
**Required Permissions**:
- Repository: Contents (read/write)
- Repository: Pull requests (read/write)
- Repository: Metadata (read)

**Token Storage**:
```
<PERSONAL_ACCESS_TOKEN_PLACEHOLDER>
```

⚠️ **SECURITY WARNING**: Never commit this file with a real token. Keep credentials in:
- Git credential manager (recommended)
- Environment variables
- `.git/config` (not committed)

---

## Initial Setup

### 1. Configure Git Identity

```powershell
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 2. Add Remote

```powershell
git remote add origin <REPOSITORY_URL>
```

### 3. Verify Remote

```powershell
git remote -v
```

Expected output:
```
origin  https://github.com/username/wifi-ac-guardian.git (fetch)
origin  https://github.com/username/wifi-ac-guardian.git (push)
```

### 4. Configure Credential Helper (Windows)

```powershell
git config --global credential.helper wincred
```

The first push will prompt for credentials. Use the Personal Access Token as the password.

---

## Common Git Commands

### Status & Inspection

```powershell
# View working tree status
git status

# View commit history
git log --oneline --graph

# View recent commits with details
git log -10

# View current branch
git branch

# View all remotes
git remote -v
```

### Staging & Committing

```powershell
# Stage all changes
git add -A

# Stage specific files
git add <file>

# Commit with message
git commit -m "type: summary"

# Amend last commit (unpushed only)
git commit --amend --no-edit
```

**Commit Message Format**:
```
<type>: <summary>

<optional body>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Syncing

```powershell
# Fetch updates from remote
git fetch

# Pull changes from remote branch
git pull

# Push local commits to remote
git push

# Push and set upstream tracking
git push -u origin <branch>
```

### Branching

```powershell
# Create new branch
git branch <branch-name>

# Switch to branch
git checkout <branch-name>

# Create and switch in one step
git checkout -b <branch-name>

# Delete local branch
git branch -d <branch-name>

# List all branches
git branch -a
```

---

## Troubleshooting

### Authentication Failed

If `git push` returns a 403 or authentication error:

1. Verify token has correct permissions
2. Regenerate token if expired
3. Clear cached credentials:
   ```powershell
   git credential-manager erase https://github.com
   ```
4. Push again — you'll be prompted for credentials

### Remote Already Exists

```powershell
# Remove existing remote
git remote remove origin

# Add correct remote
git remote add origin <REPOSITORY_URL>
```

### Diverged Branch

```powershell
# Fetch latest
git fetch

# View differences
git log origin/main..HEAD

# If safe to force push (use carefully)
git push --force-with-lease
```

---

## Protected Branches

The `main` branch may be protected with the following rules:

- ✅ Require pull request before merging
- ✅ Require status checks to pass
- ✅ Require conversation resolution before merging
- ⚠️ Direct push blocked — create feature branches instead

---

## Workflow

Standard development workflow:

1. Create feature branch: `git checkout -b 001-feature-name`
2. Make changes and commit: `git commit -m "feat: add feature"`
3. Push branch: `git push -u origin 001-feature-name`
4. Open pull request on GitHub
5. Review, approve, merge
6. Switch back to main: `git checkout main`
7. Pull latest: `git pull`
8. Delete feature branch: `git branch -d 001-feature-name`

---

## Emergency Recovery

### Undo Last Commit (Keep Changes)

```powershell
git reset --soft HEAD~1
```

### Undo Last Commit (Discard Changes)

```powershell
git reset --hard HEAD~1
```

### Recover Lost Commit

```powershell
# View reflog
git reflog

# Reset to specific commit
git reset --hard <commit-hash>
```

---

## Resources

- [GitHub Docs: Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [Git Documentation](https://git-scm.com/doc)
- [GitHub Flow Guide](https://guides.github.com/introduction/flow/)

---

**Maintained by**: Zohaib Javed (Lead Developer)  
**Last Updated**: 2026-08-05
