# CI Workflow (`ci.yml`)

## Purpose
CI runs on every push/PR to develop/main and ensures code quality before deployment.

## Triggers
- `push` on `develop`, `main`
- `pull_request` for those branches

## Jobs
1. `lint` (ruff)
2. `test` (pytest)
3. `build-and-artifacts` (wheel + Docker image + artifact upload)

## How GitHub finds it
- must be under `.github/workflows/ci.yml`
- GitHub Actions automatically parses and runs it

## Compared to `cd-develop.yml`
- CI: checks/tests/builds
- CD: deploys to dev environment
- Both can be chained with branch policies (CI first, then CD)

****Delme TODO
if you want instantly runnable CD, add workflow_dispatch: to cd-develop.yml and/or ci.yml
replace placeholder echo commands with real deploy commands (Azure login, kubectl apply)
maintain CI in PR checks before enabling CD on main branch to lower risk.
Let me know if you want me to provide a ready-to-paste cd-deploy.yml (prod) and a recommended ci.yml + cd-develop.yml policy flow diagram.
***Del me