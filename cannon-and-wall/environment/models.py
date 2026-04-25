from dataclasses import dataclass
from typing import Optional

@dataclass
class CannonAction:
    vuln_type: str        # one of: sqli, xss, broken_auth
    line_number: int
    explanation: str
    proof_of_concept: str

@dataclass
class WallAction:
    patched_code: str
    explanation: str

@dataclass
class Observation:
    source_code: str
    round: int
    stage: int
    last_cannon_report: Optional[dict]
