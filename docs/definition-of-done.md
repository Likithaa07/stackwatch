# Definition of Done

A ticket is **Done** only when every point below is true. If one is missing, the ticket stays in **In review**.

1. **Linked:** the PR says `Closes #<ticket>` and names the requirement it covers.
2. **Acceptance criteria proven:** every AC in the ticket is ticked in the PR, with evidence
   (test name, command output or screenshot).
3. **Tested:** new behaviour has automated tests; total coverage ≥ 85% (CI enforces this).
4. **Clean:** lint and format checks pass (CI enforces this).
5. **Safe:** no secrets in code or history; the secret scan passes (CI enforces this).
6. **Documented:** README, runbook or design doc updated if behaviour or operations changed.
7. **Reviewed:** the author has reviewed their own diff, and the PR checklist is complete.
8. **Merged through CI:** squash-merged into `main` with a green pipeline. No direct pushes (branch protection enforces this).
9. **Board updated:** the ticket is in **Done** on the project board.
