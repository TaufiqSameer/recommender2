from collections import defaultdict, deque

from app.db.models import SkillEdge, SkillNode


class SkillGraphValidationError(Exception):
    pass


def validate_graph(
    skills: list[SkillNode],
    edges: list[SkillEdge],
) -> None:
    skill_ids = {skill.id for skill in skills}

    for edge in edges:
        if edge.prerequisite_id not in skill_ids:
            raise SkillGraphValidationError(
                f"Unknown prerequisite: {edge.prerequisite_id}"
            )

        if edge.dependent_id not in skill_ids:
            raise SkillGraphValidationError(
                f"Unknown dependent skill: {edge.dependent_id}"
            )

    _ensure_acyclic(skill_ids, edges)


def _ensure_acyclic(
    skill_ids: set[str],
    edges: list[SkillEdge],
) -> None:
    adjacency: dict[str, list[str]] = defaultdict(list)
    indegree = {skill_id: 0 for skill_id in skill_ids}

    for edge in edges:
        adjacency[edge.prerequisite_id].append(edge.dependent_id)
        indegree[edge.dependent_id] += 1

    queue = deque(
        skill_id
        for skill_id, degree in indegree.items()
        if degree == 0
    )

    visited = 0

    while queue:
        current = queue.popleft()
        visited += 1

        for neighbor in adjacency[current]:
            indegree[neighbor] -= 1

            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if visited != len(skill_ids):
        raise SkillGraphValidationError(
            "Skill graph contains a cycle."
        )