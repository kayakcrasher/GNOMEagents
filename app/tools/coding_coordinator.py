"""Connect AI code generation to durable patch review."""

from app.tools.coding_bridge import CodingBridge
from app.tools.proposal_vault import ProposalVault
from app.tools.registry import ToolError


class CodingCoordinator:
    def __init__(self, workspace, database, model=None):
        self.bridge = CodingBridge(workspace, model=model)
        self.vault = ProposalVault(workspace, database)

    def propose_function(
        self, objective, name, parameters, path
    ):
        generated = self.bridge.propose_function(
            objective, name, parameters, path
        )

        temporary_id = generated["proposal"]["id"]

        proposal = self.bridge.patches.pending.get(
            temporary_id
        )

        if proposal is None:
            raise ToolError(
                "Generated patch was not retained"
            )

        saved = self.vault.save(
            proposal.path,
            proposal.after,
        )

        return {
            "status": "awaiting_approval",
            "proposal": saved,
            "generation": generated["generation"],
            "persistent": True,
        }

    def pending(self):
        return self.vault.pending()

    def get(self, proposal_id):
        return self.vault.get(proposal_id)
