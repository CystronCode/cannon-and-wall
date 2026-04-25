import httpx

class CannonWallClient:
    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url

    def reset(self, stage: int = 1) -> dict:
        r = httpx.post(f"{self.base_url}/reset", params={"stage": stage})
        return r.json()

    def step(self, action: dict) -> dict:
        r = httpx.post(f"{self.base_url}/step", json=action)
        return r.json()

    def state(self) -> dict:
        r = httpx.get(f"{self.base_url}/state")
        return r.json()
