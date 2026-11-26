# Git and CI Evidence Checklist

This checklist documents evidence that must be captured from GitHub and stored with the submission.

## Branches

Use the following branches as feature work is developed:

- `feature/patient-doctor-modules`
- `feature/appointment-scheduling`
- `feature/visit-billing`
- `feature/selenium-ci`

Record in Git screenshots:

1. `git branch -a`
2. A merge commit on `main`
3. The commit history with meaningful messages

## Pull requests

Create at least one pull request that is **accepted** and one pull request that is **revised or rejected**.

For the revised request, attach a short review comment showing what was changed, for example:

> The endpoint needs required-field validation and a test for the duplicate appointment response before this can be merged.

After revision, re-run tests and push the updated branch. Merge the accepted request.

## Merge conflict exercise

Use a branch to edit a README or report section while `main` edits the same section. Do not force overwrite the conflict.

1. Start a feature branch.
2. Edit one section and commit it.
3. On `main`, edit the same section differently and commit it.
4. Merge the feature branch into `main`.
5. Edit the conflict markers into the intended combined text.
6. Run tests.
7. Add and commit the resolution.

Record the conflict and resolution with screenshots or short terminal output in `docs/evidence/`.

## GitHub Actions evidence

The workflow at `.github/workflows/ci.yml` runs for push and pull-request events. Save:

- The successful workflow run
- The Python setup and dependency installation
- The pytest and coverage steps
- The commit link that triggered the run

## Repository link

Publish the repository and submit:

`https://github.com/azamsefat/Lab6`
