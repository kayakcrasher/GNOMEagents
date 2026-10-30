"""Human-controlled GNOME coding approval inbox."""

import argparse

from app.tools.proposal_vault import ProposalVault
from app.tools.registry import ToolError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=["list", "show", "approve", "reject"],
    )
    parser.add_argument("proposal_id", nargs="?")
    parser.add_argument(
        "--database",
        default=".gnome/proposals.db",
    )
    args = parser.parse_args()

    vault = ProposalVault(".", args.database)

    try:
        if args.command == "list":
            pending = vault.pending()
            print("PENDING:", len(pending))
            for item in pending:
                print(item["id"], item["path"])
            return

        if not args.proposal_id:
            parser.error("Proposal ID required")

        proposal = vault.get(args.proposal_id)
        print("STATUS:", proposal["status"])
        print("FILE:", proposal["path"])
        print(proposal["diff"])

        if args.command == "show":
            return

        if proposal["status"] != "awaiting_approval":
            print("Proposal is not pending.")
            return

        confirmation = input(
            f"Type {args.command.upper()} to confirm: "
        ).strip()

        if confirmation != args.command.upper():
            print("Cancelled. No changes applied.")
            return

        if args.command == "approve":
            result = vault.approve(
                args.proposal_id, approved=True
            )
        else:
            result = vault.reject(args.proposal_id)

        print("RESULT:", result["status"])

    except ToolError as error:
        print("ERROR:", error)


if __name__ == "__main__":
    main()
