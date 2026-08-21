import json
from pathlib import Path
from typing import Any


ROLES_FILE = (
    Path(__file__).resolve().parents[2]
    / "seed"
    / "backend_roles.json"
)


class GoalMapper:

    def __init__(
        self,
        roles_file: Path = ROLES_FILE,
    ):
        self.roles_file = roles_file
        self.data = self._load()

    def _load(self) -> dict[str, Any]:

        with self.roles_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def get_role(
        self,
        role_id: str,
    ) -> dict[str, Any] | None:

        for role in self.data["roles"]:
            if role["id"] == role_id:
                return role

        return None

    def get_required_skills(
        self,
        role_id: str,
    ) -> list[str]:

        role = self.get_role(role_id)

        if role is None:
            raise ValueError(
                f"Unknown role: {role_id}"
            )

        return role["required_skills"]

    def list_roles(self) -> list[dict[str, Any]]:

        return self.data["roles"]