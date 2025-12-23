import httpx


class Open5eClient:
    """Lightweight Open5e HTTP client (synchronous, small surface)."""

    BASE_URL = "https://api.open5e.com"

    def __init__(
        self, base_url: str = BASE_URL, timeout: float = 10.0, http_client: httpx.Client | None = None
    ) -> None:
        self.client = http_client or httpx.Client(base_url=base_url, timeout=timeout)

    def list_monsters(self, page: int = 1) -> dict:
        resp = self.client.get("/monsters/", params={"page": page})
        resp.raise_for_status()
        return resp.json()

    def get_monster(self, slug: str) -> dict:
        resp = self.client.get(f"/monsters/{slug}/")
        resp.raise_for_status()
        return resp.json()

    def list_spells(self, page: int = 1) -> dict:
        resp = self.client.get("/spells/", params={"page": page})
        resp.raise_for_status()
        return resp.json()

    def list_classes(self, page: int = 1) -> dict:
        resp = self.client.get("/classes/", params={"page": page})
        resp.raise_for_status()
        return resp.json()

    def list_races(self, page: int = 1) -> dict:
        resp = self.client.get("/races/", params={"page": page})
        resp.raise_for_status()
        return resp.json()

    def get_race(self, slug: str) -> dict:
        resp = self.client.get(f"/races/{slug}/")
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self.client.close()
