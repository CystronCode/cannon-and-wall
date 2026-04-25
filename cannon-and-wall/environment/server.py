from openenv import Environment
from pathlib import Path
from environment.models import Observation
from environment.judge.verifier import verify_cannon, verify_wall
from environment.judge.reward import cannon_reward, wall_reward

STAGE_FILES = {
    1: "environment/vulnerable_app/stage_1/app.py"
}
GROUND_TRUTH = {
    1: {"vuln_type": "sqli", "line_number_range": [10, 20]}
}

class CannonWallEnvironment(Environment):
    def reset(self, stage: int = 1):
        source = Path(STAGE_FILES[stage]).read_text()
        self.state = {
            "round": 1,
            "stage": stage,
            "source_code": source,
            "scores": {"cannon": 0.0, "wall": 0.0},
            "last_cannon_report": None
        }
        return self.state

    def step(self, action: dict):
        agent = action.get("agent")
        if agent == "cannon":
            v = verify_cannon(action)
            if not v["valid"]:
                return {"reward": 0, "issues": v["issues"]}
            r = cannon_reward(action, GROUND_TRUTH[self.state["stage"]])
            self.state["scores"]["cannon"] += r
            self.state["last_cannon_report"] = action
            return {"reward": r, "valid": True}
        elif agent == "wall":
            test_results = verify_wall(
                action.get("patched_code", ""),
                self.state["stage"]
            )
            r = wall_reward(action.get("patched_code",""), [], test_results)
            self.state["scores"]["wall"] += r
            self.state["round"] += 1
            return {"reward": r, "test_results": test_results}
        return {"error": "unknown agent"}
