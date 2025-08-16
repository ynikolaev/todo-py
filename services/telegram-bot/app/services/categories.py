from pydantic import BaseModel

from app.infra.http import api_client

from .telegram import TelegramAccountDTO


class CategoryDTO(BaseModel):
    id: int | None = None
    name: str = ""
    tg: TelegramAccountDTO | None = None


class CategoryService:
    def __init__(self, api_token: str):
        self._api_client = api_client
        self._token = api_token

    async def get_categories(
        self, page: int = 1, page_size: int = 20, user_id: str = ""
    ) -> dict:
        async with self._api_client(self._token) as client:
            r = await client.get(
                "api/categories/",
                params={"page": page, "page_size": page_size, "tg_user_id": user_id},
            )
            if r.status_code != 200:
                return self._format_error(r)
        return r.json()

    async def create_category(self, category: CategoryDTO) -> dict:
        async with self._api_client(self._token) as client:
            r = await client.post(
                "api/categories/", json=category.model_dump(exclude_unset=True)
            )
        if r.status_code != 201:
            return self._format_error(r)
        return r.json()

    async def update_category(self, category_id: int, category: CategoryDTO) -> dict:
        async with self._api_client(self._token) as client:
            r = await client.put(
                f"api/categories/{category_id}/",
                json=category.model_dump(exclude_unset=True),
            )
        if r.status_code != 200:
            return self._format_error(r)
        return r.json()

    async def delete_category(self, category_id: str) -> dict | bool:
        async with self._api_client(self._token) as client:
            r = await client.delete(f"api/categories/{category_id}/")
        if r.status_code not in (200, 204):
            return self._format_error(r)
        return True

    def _format_error(self, response) -> dict[str, str]:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        if isinstance(detail, dict):
            error_message = "\n".join(f"{k}: {v}" for k, v in detail.items())
        elif isinstance(detail, list):
            error_message = "\n".join(detail)
        else:
            error_message = str(detail)
        return {"error": error_message}
