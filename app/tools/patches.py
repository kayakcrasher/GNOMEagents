"""Reviewable, single-file workspace patches."""

import difflib
import hashlib
import secrets
from dataclasses import dataclass
from pathlib import Path

from app.tools.registry import ToolError, ToolRegistry


@dataclass(frozen=True)
class PatchProposal:
    id: str
    path: str
    before_hash: str
    after: str
    diff: str


class PatchManager:
    MAX_BYTES = 65536

    def __init__(self, workspace):
        self.registry = ToolRegistry(workspace)
        self.pending = {}

    @staticmethod
    def digest(content):
        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

    def _target(self, path):
        if not isinstance(path, str) or not path:
            raise ToolError("File path required")

        target = self.registry.resolve(path)

        if target.is_symlink():
            raise ToolError("Symlink changes denied")

        if not target.is_file():
            raise ToolError("Existing file required")

        if target.stat().st_size > self.MAX_BYTES:
            raise ToolError("File too large")

        return target

    def propose(self, path, new_content):
        if not isinstance(new_content, str):
            raise ToolError("Text content required")

        if len(new_content.encode("utf-8")) > self.MAX_BYTES:
            raise ToolError("Proposed content too large")

        target = self._target(path)
        before = target.read_text(encoding="utf-8")

        if before == new_content:
            raise ToolError("No changes proposed")

        relative = str(
            target.relative_to(self.registry.root)
        )

        diff = "".join(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile="before/" + relative,
                tofile="after/" + relative,
            )
        )

        proposal = PatchProposal(
            id=secrets.token_hex(16),
            path=relative,
            before_hash=self.digest(before),
            after=new_content,
            diff=diff,
        )

        self.pending[proposal.id] = proposal

        return {
            "id": proposal.id,
            "path": proposal.path,
            "diff": proposal.diff,
            "status": "awaiting_approval",
        }

    def apply(self, proposal_id, approved=False):
        if not approved:
            raise ToolError("Explicit approval required")

        proposal = self.pending.get(proposal_id)

        if proposal is None:
            raise ToolError("Unknown proposal")

        target = self._target(proposal.path)
        current = target.read_text(encoding="utf-8")

        if self.digest(current) != proposal.before_hash:
            raise ToolError("File changed since proposal")

        target.write_text(
            proposal.after,
            encoding="utf-8",
        )

        self.pending.pop(proposal_id)

        return {
            "path": proposal.path,
            "status": "applied",
        }
