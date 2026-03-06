---
title: "Access Control Guide"
parent: General
grand_parent: English
nav_order: 7
---

# Access Control & Permission Management

This guide explains how to manage access control for the Kugelpos documentation site using GitHub features.

---

## 1. Repository Visibility

| Setting | Effect on GitHub Pages |
|---------|----------------------|
| **Public** | Documentation is accessible to everyone on the internet |
| **Private** | Only repository collaborators can access (GitHub Enterprise required for Pages) |
| **Internal** (Enterprise) | Accessible within the organization only |

### How to Change

1. Go to **Repository Settings** → **General**
2. Scroll to **Danger Zone** → **Change repository visibility**

---

## 2. GitHub Pages Access Control

### Public Repositories
- Pages are always publicly accessible
- No additional access control available

### Private Repositories (GitHub Enterprise Cloud)
- Pages can be restricted to organization members
- Settings → **Pages** → **Access control** → select **Private**

### Recommended Setup

| Environment | Visibility | Pages Access |
|-------------|-----------|-------------|
| Development | Private | Restricted to team |
| Production | Public or Internal | Organization-wide |

---

## 3. Branch Protection Rules

Protect the `main` branch to ensure documentation quality:

### Recommended Rules

1. **Require pull request reviews**
   - Minimum 1 approving review
   - Dismiss stale pull request approvals

2. **Require status checks to pass**
   - Require the Jekyll build check to pass before merge

3. **Restrict who can push**
   - Only designated maintainers can push directly

### How to Configure

1. Go to **Repository Settings** → **Branches**
2. Click **Add rule** for `main` branch
3. Enable the desired protections

---

## 4. CODEOWNERS for Documentation

Create a `CODEOWNERS` file to require reviews for documentation changes:

```
# .github/CODEOWNERS

# Documentation requires review from docs team
/docs/ @org-name/docs-team

# GitHub Actions workflows require DevOps review
/.github/workflows/ @org-name/devops-team

# Service-specific docs require respective team review
/docs/en/account/ @org-name/account-team
/docs/en/cart/ @org-name/cart-team
/docs/en/terminal/ @org-name/terminal-team
/docs/en/master-data/ @org-name/masterdata-team
/docs/en/report/ @org-name/report-team
/docs/en/journal/ @org-name/journal-team
/docs/en/stock/ @org-name/stock-team
```

---

## 5. GitHub Teams & Roles

### Recommended Team Structure

| Team | Repository Role | Permissions |
|------|----------------|-------------|
| `docs-admin` | Admin | Full control, manage settings |
| `docs-maintainer` | Maintain | Manage issues, PRs, merge |
| `docs-writer` | Write | Push to feature branches, create PRs |
| `docs-reader` | Read | View documentation only |

### Role Capabilities

| Action | Read | Write | Maintain | Admin |
|--------|------|-------|----------|-------|
| View docs | ✅ | ✅ | ✅ | ✅ |
| Create PRs | ❌ | ✅ | ✅ | ✅ |
| Merge PRs | ❌ | ❌ | ✅ | ✅ |
| Manage settings | ❌ | ❌ | ❌ | ✅ |
| Deploy Pages | ❌ | ❌ | ✅ | ✅ |

---

## 6. Workflow Permissions

The GitHub Actions workflows use minimal permissions:

```yaml
# jekyll-gh-pages.yml
permissions:
  contents: read    # Read repository
  pages: write      # Deploy to Pages
  id-token: write   # OIDC token for deployment

# generate-docs.yml
permissions:
  contents: write   # Commit generated docs
```

### Security Best Practices

1. **Use `GITHUB_TOKEN`** - Automatically scoped to the repository
2. **Avoid storing secrets** unless necessary
3. **Review third-party actions** before using
4. **Pin action versions** using SHA hashes for production

---

## 7. Quick Setup Checklist

- [ ] Set repository visibility (Public/Private)
- [ ] Enable GitHub Pages (Settings → Pages → Source: GitHub Actions)
- [ ] Configure branch protection for `main`
- [ ] Create `CODEOWNERS` file
- [ ] Set up GitHub Teams with appropriate roles
- [ ] Review workflow permissions
- [ ] Test the deployment pipeline
