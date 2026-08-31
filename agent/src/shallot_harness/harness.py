"""SHALLOT Harness orchestrator — wires ledger, context, policy, memory, reasoner."""

from pathlib import Path

from shallot_harness.context.git import GitContext
from shallot_harness.context.github import GitHubContext
from shallot_harness.context.repo import RepoContext
from shallot_harness.ledger import ProjectLedger
from shallot_harness.memory import MemoryStore
from shallot_harness.models import ProjectEvent, ProjectState, Provenance
from shallot_harness.policy import Action, PolicyGate
from shallot_harness.reasoner import Reasoner, ReasonerRequest


class Harness:
    """Single entry point. Read context → reason → gate → record → remember."""

    def __init__(
        self,
        project_id: str,
        repo_path: str,
        db_path: str,
        reasoner: Reasoner,
        policy: PolicyGate | None = None,
        memory: MemoryStore | None = None,
    ) -> None:
        self.project_id = project_id
        self._repo_path = repo_path
        self._git = GitContext(repo_path)
        self._github = GitHubContext(repo_path)
        self._repo = RepoContext(repo_path)
        self._ledger = ProjectLedger(db_path)
        self._reasoner = reasoner
        self._policy = policy or PolicyGate()
        self._memory = memory or MemoryStore()
        self._last_next_action = None
        self._loop_count = 0

    def current_state(self) -> ProjectState | None:
        return self._ledger.state(self.project_id)

    def request_approval(self, kind: str, target: str, payload: dict | None = None) -> bool:
        """HITL gate for a pending action (UX research 5.4).

        Returns True if the action is auto-approved and may run immediately.
        Returns False if it requires human approval and is now pending in the
        ApprovalStore — the caller must NOT execute the side effect and should
        tell the user to resolve it via approve_action. Raises nothing; callers
        check the boolean. Use for memory writes, code writes, PRs, etc.
        """
        action = Action.create(kind, target, payload)
        verdict = self._policy.check(action)
        return verdict.allowed

    def run(self, goal: str = "Continue SHALLOT prototype development") -> dict:
        """Full lifecycle: context → reason → gate → record → remember."""
        git = self._git.state()
        issues = self._github.issues()
        memories = self._memory.query(scope="workspace:shallot")

        request = ReasonerRequest(
            project_id=self.project_id,
            current_issue=self.current_state().current_issue if self.current_state() else None,
            git_branch=git.branch,
            git_head=git.head_sha,
            dirty=git.dirty,
            recent_commits=[c.short_message for c in git.recent_commits],
            open_issues=[f"#{i.number}: {i.title}" for i in issues],
            memory_context=[m.content for m in memories],
            goal=goal,
        )

        response = self._reasoner.reason(request)

        action = Action.create(
            kind=response.action_kind,
            target=response.target,
            payload={"next_action": response.next_action, "reasoning": response.reasoning},
        )

        verdict = self._policy.check(action)

        new_state = ProjectState(
            project_id=self.project_id,
            current_issue=request.current_issue,
            next_action=response.next_action,
            verification_criterion=response.reasoning,
            observed_at=action.requested_at,
        )

        next_action = response.next_action
        if next_action == self._last_next_action:
            self._loop_count += 1
        else:
            self._loop_count = 0
        self._last_next_action = next_action

        if self._loop_count >= 3:
            return {
                "state": new_state,
                "action": action,
                "verdict": verdict,
                "response": response,
                "loops_detected": True,
                "loop_message": f"Harness stopped: next_action repeated {self._loop_count} times. Consider changing strategy or getting human input.",
            }

        provenance = Provenance(
            actor="shallot-harness",
            method="system",
            initiated_at=action.requested_at,
        )

        self._ledger.append(ProjectEvent.status_recorded(new_state, provenance=provenance))

        return {
            "state": new_state,
            "action": action,
            "verdict": verdict,
            "response": response,
        }

    def close(self) -> None:
        self._ledger.close()
