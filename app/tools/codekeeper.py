"""Codekeeper: persistent, review-first coding tasks."""

from app.tools.devops import DevOpsTools
from app.tools.engine import AgentEngine
from app.tools.journal import AgentJournal
from app.tools.patches import PatchManager
from app.tools.planner import WorkspacePlanner
from app.tools.registry import ToolRegistry, ToolError


class Codekeeper:
    def __init__(self, workspace, database):
        self.registry = ToolRegistry(workspace)
        self.journal = AgentJournal(database)
        self.patches = PatchManager(workspace)

    def prepare(self, objective, path, new_content):
        task = self.journal.create_task(
            objective,
            self.registry.root,
        )
        task_id = task["id"]

        self.journal.transition(task_id, "running")

        try:
            engine = AgentEngine(
                self.registry,
                WorkspacePlanner(),
            )

            state = engine.run(objective)

            for observation in state.observations:
                self.journal.record(
                    task_id,
                    "tool.observation",
                    observation,
                )

            if state.status != "completed":
                raise ToolError(
                    "Workspace inspection failed"
                )

            proposal = self.patches.propose(
                path,
                new_content,
            )

            self.journal.record(
                task_id,
                "patch.proposed",
                {
                    "proposal_id": proposal["id"],
                    "path": proposal["path"],
                    "diff": proposal["diff"],
                },
            )

            self.journal.transition(
                task_id,
                "awaiting_approval",
            )

            return {
                "task_id": task_id,
                "status": "awaiting_approval",
                "proposal": proposal,
            }

        except Exception as error:
            self.journal.record(
                task_id,
                "task.failed",
                {"error": str(error)},
            )
            self.journal.transition(
                task_id, "failed"
            )
            raise

    def approve(self, task_id, proposal_id):
        """Apply an approved patch and verify the result."""
        task = self.journal.get_task(task_id)

        if task["status"] != "awaiting_approval":
            raise ToolError("Task is not awaiting approval")

        proposals = [
            event["payload"]["proposal_id"]
            for event in self.journal.history(task_id)
            if event["kind"] == "patch.proposed"
        ]

        if proposal_id not in proposals:
            raise ToolError(
                "Proposal does not belong to task"
            )

        result = self.patches.apply(
            proposal_id,
            approved=True,
        )

        self.journal.record(
            task_id,
            "patch.applied",
            result,
        )

        self.journal.transition(task_id, "running")

        tools = DevOpsTools(self.registry.root)

        try:
            tests = tools.run_tests()

            self.journal.record(
                task_id,
                "verification.tests",
                tests,
            )

            if not tests["passed"]:
                self.journal.transition(
                    task_id, "failed"
                )
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "reason": "Tests did not pass",
                    "tests": tests,
                }

            # Git inspection is informative. A non-Git
            # workspace can still pass verification.
            try:
                git = {
                    "status": tools.git_status(),
                    "diff": tools.git_diff(),
                }
            except ToolError as error:
                git = {
                    "available": False,
                    "reason": str(error),
                }

            self.journal.record(
                task_id,
                "verification.git",
                git,
            )

            self.journal.transition(
                task_id, "completed"
            )

            return {
                "task_id": task_id,
                "status": "completed",
                "patch": result,
                "tests": tests,
                "git": git,
            }

        except Exception as error:
            self.journal.record(
                task_id,
                "verification.error",
                {"error": str(error)},
            )
            self.journal.transition(
                task_id, "failed"
            )
            raise
