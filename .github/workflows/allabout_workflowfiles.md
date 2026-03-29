✅ What ci.yml does (novice explanation)
Great news: this workflow is a typical “Continuous Integration” pipeline that checks your code quality, tests it, and builds artefacts each time you push or open/refresh PR.

Trigger
on: push to develop or main
on: pull_request targeting develop or main
So every code change in those branches or PRs runs checks automatically.

Jobs (steps that run in order)
lint

runs on GitHub-hosted Linux (ubuntu-latest)
checks out repo
installs Python 3.13
installs tools: ruff, pytest
runs static checks: ruff check .
test

depends on lint (needs: lint)
checks out repo
sets up Python 3.13
installs package in development mode: pip install -e .[test]
runs tests: pytest -q
build-and-artifacts

depends on test
checks out repo
setup Python 3.13
installs build tooling: build, twine
builds Python wheel to dist
builds Docker image tagged by commit SHA
generates SBOM + image signature (placeholders)
uploads artifacts to GitHub Actions artifact storage
🧰 Why workflows and how GitHub recognizes it
.github folder: special config area for GitHub features (Actions, issue templates, etc.).
workflows subfolder: reserved for workflow files.
GitHub scans for *.yml/*.yaml under workflows.
Each file with valid structure (name, on, jobs) becomes a workflow.
It’s hidden because folder name starts .; this means config metadata and doesn’t clutter root code.
🆚 Compare ci.yml vs cd-develop.yml
Similarities
both are GitHub Actions YAMLs in workflows
both use ubuntu-latest runners
both use actions/checkout@v4
both are triggered by commits on develop (CI adds main + PR too)
Differences
ci.yml is validation-focused:
lint
test
build artifacts
no deploy
designed to stop early on errors
cd-develop.yml is deployment-focused:
build image
push to registry (placeholder)
deploy to dev cluster (placeholder)
no lint/test formally (assumes CI already ran)
ci.yml has job dependencies:
test waits for lint
build-and-artifacts waits for test
cd-develop.yml has deploy dependency:
deploy-dev waits for build-and-push
Purpose
ci.yml = quality gate / early failure (prevent bad code from merging)
cd-develop.yml = operational pipeline (deploy code to dev environment)

if you want instantly runnable CD, add workflow_dispatch: to cd-develop.yml and/or ci.yml
replace placeholder echo commands with real deploy commands (Azure login, kubectl apply)
maintain CI in PR checks before enabling CD on main branch to lower risk.


🆚 Workflow comparison (all three: ci.yml, cd-develop.yml, cd-main.yml)
Workflow	Trigger	Purpose	Risk Level
ci.yml	Auto push/PR on develop/main	Lint, test, build	Low (no deploy)
cd-develop.yml	Auto push on develop	Build + deploy to dev AKS	Medium (dev only)
cd-main.yml	Manual + approval	Promote to prod AKS	High (production)


Perfect: I can see you're viewing `cd-main.yml` right now. Let me read it and provide a full novice explanation with the wiki docs. 

Read [](file:///c%3A/Users/henley/Documents/Dev/mypy/ticmymail/.github/workflows/cd-main.yml)

## ✅ What cd-main.yml does (novice explanation)

Excellent: this is a production deployment pipeline that runs **manually on demand** instead of automatically.  
It promotes a pre-built image from `develop` and deploys it to production with human approval.

### Key difference from `cd-develop.yml`
- `cd-develop.yml` runs automatically on every push to `develop`
- cd-main.yml runs manually when someone clicks a button and approves it

### Trigger
- `on: workflow_dispatch`
- This adds a "Run workflow" button in GitHub Actions UI
- User provides input: `promote_image` (which image from dev builds to move to prod)

### The Job: `promote-and-deploy`

1. **Manual approval (placeholder)**
   - Uses `slash-command-dispatch` action
   - expects a `/approve` comment from authorized users
   - this is a safety gate before production

2. **Pull image from ACR (placeholder)**
   - retrieves the specific image tag from container registry
   - example: if `promote_image = "develop-abc123"`, pull that image

3. **Deploy to AKS prod namespace (placeholder)**
   - runs `kubectl apply` against production manifests
   - uses real Kubernetes commands (placeholder shows intent)

4. **Verify deployment (placeholder)**
   - checks rollout status in production
   - confirms pods are running healthy

---

## 🧪 Why workflows and how GitHub recognizes it

Same reason as before:
- .github = reserved GitHub config folder
- `workflows` = reserved subfolder for GitHub Actions automation
- GitHub scans all `*.yml`/`*.yaml` files in workflows
- If they have valid structure (`name`, `on`, `jobs`), GitHub registers them as workflows
- Folder hidden (`.` prefix) = config metadata, not app code

---

## 📘 Wiki file: `cd-main.md`

Here's what to add as `.github/workflows/cd-main.md` (note: you named it `ci-main.md`, but this is a **CD** file for production, not CI—I'll explain both):

```markdown
# CD Main Workflow (`cd-main.yml`)

## Purpose
Manual production deployment gate. Allows authorized users to promote a tested image from develop direct to production with explicit approval.

## Trigger
- `workflow_dispatch` — requires manual button click in GitHub Actions UI
- Input parameter: `promote_image` (required)
  - Example: `develop-abc123def456` (commit SHA from develop build)

## Jobs
### `promote-and-deploy`
1. Manual approval (check for `/approve` comment)
2. Pull pre-built image from container registry
3. Deploy to AKS production namespace
4. Verify rollout status

## Process Flow
1. Developer clicks "Run workflow" in Actions tab
2. Enters image tag (e.g., `develop-abc123`) from a successful `cd-develop` run
3. System waits for approver to comment `/approve` on the workflow PR
4. Once approved, image is pulled and deployed to production
5. Rollout verification confirms healthy pods

## Why Manual?
- Production is high-risk; you don't want automatic deploys
- humans review and explicitly approve
- audit trail: who approved, when, which image

## Difference from `cd-develop.yml`
- `cd-develop`: automatic on push develop, no approval
- `cd-main`: manual trigger, explicit approval required

## Next Steps
- Replace placeholder ACR login with real credentials
- Replace kubectl commands with actual manifest paths
- Ensure GitHub secrets are configured for registry/cluster access
```

---

## 🆚 Workflow comparison (all three: ci.yml, `cd-develop.yml`, cd-main.yml)

| Workflow | Trigger | Purpose | Risk Level |
|----------|---------|---------|-----------|
| ci.yml | Auto push/PR on develop/main | Lint, test, build | Low (no deploy) |
| `cd-develop.yml` | Auto push on develop | Build + deploy to dev AKS | Medium (dev only) |
| cd-main.yml | Manual + approval | Promote to prod AKS | High (production) |

---

## 💡 Recommended team workflow

1. Developer pushes to branch
2. GitHub runs ci.yml (lint/test)
3. PR reviewed and merged to `develop`
4. `cd-develop.yml` auto-deploys to dev cluster
5. Team tests in dev
6. When ready: manually trigger cd-main.yml + approve
7. Goes live on production

This keeps mistakes out of production. Let me know if you want a visual diagram of this flow!