# environment/server.py — FIXED
# Imports now match actual function names in verifier.py and reward.py
 
from openenv import Environment
from pathlib import Path
 
from environment.models import GameState
from environment.judge.verifier import verify_cannon_report, verify_patch
from environment.judge.reward import calculate_rewards
 
STAGE_FILES = {
    1: "environment/vulnerable_app/stage_1/app.py",
    2: "environment/vulnerable_app/stage_2/app.py",
    3: "environment/vulnerable_app/stage_3/app.py",
}
 
MAX_ROUNDS = 3
 
 
class CannonWallEnvironment(Environment):
 
    def reset(self, stage: int = 1):
        source = Path(STAGE_FILES[stage]).read_text()
        self.state = {
            "round":               1,
            "stage":               stage,
            "source_code":         source,
            "original_source":     source,          # preserved for bypass phase
            "phase":               "attack",         # attack → patch → bypass → done
            "scores":              {"cannon": 0.0, "wall": 0.0},
            "last_cannon_report":  None,
            "last_wall_patch":     None,
            "done":                False,
        }
        return {
            "phase":       self.state["phase"],
            "round":       self.state["round"],
            "stage":       self.state["stage"],
            "source_code": self.state["source_code"],
        }
 
    def step(self, action: dict):
        if self.state.get("done"):
            return {"error": "episode is done — call reset() to start a new one"}
 
        agent = action.get("agent")
        phase = self.state["phase"]
 
        # ── ATTACK phase: Cannon finds a vulnerability ──────────────────────
        if agent == "cannon" and phase == "attack":
            verification = verify_cannon_report(action, self.state["stage"])
 
            # Partial reward signal even on failure so training isn't starved
            dummy_wall = {
                "sqli_fixed": False, "xss_fixed": False,
                "broken_auth_fixed": False,
                "functionality_preserved": False,
                "new_vulns_introduced": False,
            }
            dummy_bypass = {"real_vuln_found": False, "correct_vuln_type": False}
            rewards = calculate_rewards(verification, dummy_wall, dummy_bypass)
 
            self.state["last_cannon_report"] = action
            self.state["scores"]["cannon"] += rewards["cannon_raw"]
            self.state["phase"] = "patch"
 
            return {
                "reward":      rewards["cannon_total"],
                "cannon_raw":  rewards["cannon_raw"],
                "breakdown":   rewards["breakdown"],
                "phase":       self.state["phase"],
                "observation": {
                    "phase":          self.state["phase"],
                    "round":          self.state["round"],
                    "stage":          self.state["stage"],
                    "source_code":    self.state["source_code"],
                    "cannon_report":  action,
                },
            }
 
        # ── PATCH phase: Wall patches the vulnerability ──────────────────────
        elif agent == "wall" and phase == "patch":
            patched_code = action.get("patched_code", "")
            vuln_type = (self.state["last_cannon_report"] or {}).get("vuln_type", "sqli")
 
            patch_verification = verify_patch(
                self.state["original_source"],
                patched_code,
                vuln_type,
            )
 
            dummy_cannon  = {"real_vuln_found": False, "correct_vuln_type": False}
            dummy_bypass  = {"real_vuln_found": False, "correct_vuln_type": False}
            rewards = calculate_rewards(dummy_cannon, patch_verification, dummy_bypass)
 
            self.state["last_wall_patch"] = patched_code
            self.state["source_code"]     = patched_code   # Cannon sees patched code next
            self.state["scores"]["wall"] += rewards["wall_raw"]
            self.state["phase"] = "bypass"
 
            return {
                "reward":         rewards["wall_total"],
                "wall_raw":       rewards["wall_raw"],
                "test_results":   patch_verification,
                "breakdown":      rewards["breakdown"],
                "phase":          self.state["phase"],
                "observation": {
                    "phase":          self.state["phase"],
                    "round":          self.state["round"],
                    "stage":          self.state["stage"],
                    "source_code":    self.state["original_source"],  # original for bypass
                    "patched_code":   patched_code,
                },
            }
 
        # ── BYPASS phase: Cannon tries to beat Wall's patch ──────────────────
        elif agent == "cannon" and phase == "bypass":
            bypass_verification = verify_cannon_report(action, self.state["stage"])
 
            attack_v = verify_cannon_report(
                self.state["last_cannon_report"] or {}, self.state["stage"]
            )
            patch_v = verify_patch(
                self.state["original_source"],
                self.state["last_wall_patch"] or "",
                (self.state["last_cannon_report"] or {}).get("vuln_type", "sqli"),
            )
            rewards = calculate_rewards(attack_v, patch_v, bypass_verification)
 
            self.state["scores"]["cannon"] += rewards["cannon_raw"]
            self.state["scores"]["wall"]   += rewards["wall_raw"]
            self.state["round"] += 1
 
            # Episode ends after MAX_ROUNDS or if a score goes deeply negative
            done = (
                self.state["round"] > MAX_ROUNDS or
                self.state["scores"]["cannon"] < -15.0 or
                self.state["scores"]["wall"]   < -15.0
            )
            self.state["phase"] = "done" if done else "attack"
            self.state["done"]  = done
 
            # Reset source_code back to original for next attack round
            if not done:
                self.state["source_code"]    = self.state["original_source"]
                self.state["last_cannon_report"] = None
                self.state["last_wall_patch"]    = None
 
            return {
                "reward": {
                    "cannon_total": rewards["cannon_total"],
                    "wall_total":   rewards["wall_total"],
                    "cannon_raw":   rewards["cannon_raw"],
                    "wall_raw":     rewards["wall_raw"],
                },
                "breakdown":    rewards["breakdown"],
                "done":         done,
                "round_scores": self.state["scores"],
                "phase":        self.state["phase"],
                "observation": {
                    "phase":  self.state["phase"],
                    "round":  self.state["round"],
                    "stage":  self.state["stage"],
                    "source_code": self.state["source_code"],
                },
            }
 
        # ── Unknown agent or wrong phase ─────────────────────────────────────
        return {
            "error": f"Unexpected agent='{agent}' in phase='{phase}'. "
                     f"Expected: attack→cannon, patch→wall, bypass→cannon."
        }