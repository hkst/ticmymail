# CD Deploy Workflow

This document describes `cd-deploy.yml`, the production deployment pipeline.

## Why `.github/workflows`?
GitHub Actions discovers workflows in this folder automatically.
It is part of GitHub repository automation configuration.

## Trigger
- `push` to `main` (or `release/*`)
- Optionally `workflow_dispatch` for manual trigger

## Jobs
### `build-and-push`
- checkout code
- set up Docker Buildx
- build Docker image
- authenticate to container registry
- push image to private registry

### `deploy-prod`
- ensure build completed
- apply Kubernetes manifests in `manifests/prod`
- verify deployment rollout status

## Placeholders
- `Login to ACR (placeholder)` means "replace with real service login"
- `kubectl apply ... (placeholder)` means "replace with real Kubernetes deploy commands"

## Why use GitHub Actions
- consistent, repeatable deploy process
- audit trail for every deploy
- no manual command errors
- easy rollback by checking previous commit/PR

## “Hidden” folder logic
`.github` is root config folder.
`workflows` is the branch where GitHub Actions config lives.
GitHub automatically picks up files here.

## How to use
1. commit workflow file
2. push branch
3. go to repository -> Actions -> `CD Deploy`
4. observe run logs and status


## Follow-up suggestion
Keep placeholders replaced with real docker login / push and kubectl commands once target infra is configured.

