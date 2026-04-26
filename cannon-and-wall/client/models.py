from pydantic import BaseModel
from typing import Optional

class CannonAction(BaseModel):
    vuln_type: str          # "sqli" | "xss" | "broken_auth"
    line_number: int        # line where vuln was found
    proof_of_concept: str = ""   # add this after line_number field
    patched_code: str       # Cannon's attempted bypass patch

class WallAction(BaseModel):
    patched_code: str       # Wall's security patch

class GameState(BaseModel):
    stage: int              # 1=easy, 2=medium, 3=hard
    original_code: str      # vulnerable app.py content
    round: int              # current round (1–3, then episode ends)
    cannon_report: Optional[dict] = None
    wall_patch: Optional[str] = None

class StepResult(BaseModel):
    observation: dict
    reward: dict            # {"cannon_total": float, "wall_total": float, ...}
    done: bool
    info: dict

class ResetResult(BaseModel):
    observation: dict
    state: GameState
