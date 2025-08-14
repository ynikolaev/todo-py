from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from app.infra.http import api_client


# ----- Local DTOs (mirror your DRF serializer) -----
@dataclass
class TaskDTO:
    id: int
    user_id: int
    title: str
    due_date: date | None
    is_done: bool

    @staticmethod
    def from_json(obj: dict) -> TaskDTO:
        # Accepts ISO date or null
        due = obj.get("due_date")
        return TaskDTO(
            id=int(obj["id"]),
            user_id=int(obj["user_id"]),
            title=str(obj["title"]),
            due_date=date.fromisoformat(due) if due else None,
            is_done=bool(obj.get("is_done", False)),
        )


# ----- CRUD via Django REST API -----


async def create_task(
    *,
    user_id: int,
    title: str,
    due_date: date | None,
) -> TaskDTO:
    """
    POST /api/tasks/
    Body: { user_id, title, due_date }
    """
    payload = {
        "user_id": user_id,
        "title": title,
        "due_date": due_date.isoformat() if due_date else None,
    }
    async with api_client() as client:
        resp = await client.post("/api/tasks/", json=payload)
        resp.raise_for_status()
        return TaskDTO.from_json(resp.json())


async def list_tasks(
    *,
    user_id: int,
    include_done: bool = False,
    limit: int = 50,
) -> Sequence[TaskDTO]:
    """
    GET /api/tasks/?user_id=...&is_done=...&limit=...
    Adjust params to match your DRF view (e.g., filtering by request.user instead).
    """
    params = {
        "user_id": user_id,  # if your API filters server-side by auth user, you can drop this
        "limit": limit,
    }
    if not include_done:
        params["is_done"] = "false"

    async with api_client() as client:
        resp = await client.get("/api/tasks/", params=params)
        resp.raise_for_status()
        data = resp.json()
        # If your API is paginated (DRF default), data might be { "results": [...] }
        items = (
            data["results"] if isinstance(data, dict) and "results" in data else data
        )
        return [TaskDTO.from_json(it) for it in items]


async def complete_task(
    *,
    user_id: int,
    task_id: int,
) -> bool:
    """
    PATCH /api/tasks/{id}/  { "is_done": true }
    (If you expose a custom action, e.g., POST /api/tasks/{id}/complete/, swap accordingly.)
    """
    async with api_client() as client:
        resp = await client.patch(f"/api/tasks/{task_id}/", json={"is_done": True})
        if resp.status_code == 404:
            return False
        resp.raise_for_status()
        return True
