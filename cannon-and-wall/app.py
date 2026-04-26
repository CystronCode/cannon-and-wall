from environment.server import CannonWallEnvironment
import uvicorn
from fastapi import FastAPI

api = FastAPI()
env = CannonWallEnvironment()

@api.post("/reset")
def reset(stage: int = 1):
    return env.reset(stage=stage)

@api.post("/step")
def step(action: dict):
    return env.step(action)

@api.get("/state")
def state():
    return env.state

if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=7860)
