# CI/CD Automation Toolkit

Bulk GitHub Actions workflows, job application automation, and CI/CD run reports.

## What's included

### Workflows (`/workflows`)
- `rust.yml` — cargo build/test/clippy/fmt
- `python.yml` — pip install, pytest/unittest, py_compile
- `node.yml` — npm ci, build, lint, test
- `podman-build.yml` — Red Hat Podman build + push to GHCR
- `generic.yml` — placeholder for repos without specific tooling

### Results (`/results`)
- `workflow-trigger-results.txt` — 699 workflow triggers across ~190 repos
- `final-ci-summary.md` — complete CI run summary
- `failed-repo-debug.txt` — failure analysis
- `final-fix-results.txt` — fix verification results

### Scripts (`/scripts`)
- `ai_job_auto_apply.py` — Playwright-based job application automation
- `send_all_applications.py` — email-based application fallback

### Templates (`/templates`)
- `ats_applicant_profile.json` — applicant profile template
- `cover-letters/` — personalized cover letters for AI/remote roles

## Usage

1. Copy desired workflow into `.github/workflows/` in your repo
2. Commit and push
3. GitHub Actions runs automatically

## License

MIT
