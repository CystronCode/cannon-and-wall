# judge/reward.py — V2 (novelty bonus, per-component breakdown for W&B)

# --- Normalization constants ---
# Cannon: min = false_positive (-5), max = real+correct+bypass+novel (+32)
CANNON_MIN, CANNON_MAX = -5.0, 32.0

# Wall: min = no_fixes + new_vulns + bypassed (-10), max = all_fixes + func + held (+25)
WALL_MIN, WALL_MAX = -10.0, 25.0


def calculate_rewards(
    cannon_attack_verification: dict,
    wall_patch_verification: dict,
    cannon_bypass_verification: dict,
) -> dict:
    """
    Calculate normalized rewards for Cannon and Wall agents.

    Returns a dict with:
      cannon_total        — normalized [0, 1]
      wall_total          — normalized [0, 1]
      cannon_raw          — raw score
      wall_raw            — raw score
      breakdown           — per-component dict (log each key to W&B as its own column)
    """
    cannon_reward = 0.0
    wall_reward   = 0.0
    breakdown     = {}

    # ---- Cannon attack phase ----
    if cannon_attack_verification.get("real_vuln_found", False):
        cannon_reward += 10.0
        breakdown["attack_real_vuln_found"] = 10.0
        if cannon_attack_verification.get("correct_vuln_type", False):
            cannon_reward += 5.0
            breakdown["attack_correct_vuln_type"] = 5.0
    else:
        cannon_reward -= 5.0
        breakdown["attack_false_positive"] = -5.0

    # Novelty bonus: reward Cannon for using a new exploit pattern
    if cannon_attack_verification.get("exploit_novel", False):
        cannon_reward += 2.0
        breakdown["attack_exploit_novelty"] = 2.0
    else:
        breakdown["attack_exploit_novelty"] = 0.0

    # ---- Wall patch phase ----
    if wall_patch_verification.get("sqli_fixed", False):
        wall_reward += 5.0
        breakdown["wall_sqli_fixed"] = 5.0
    else:
        breakdown["wall_sqli_fixed"] = 0.0

    if wall_patch_verification.get("xss_fixed", False):
        wall_reward += 5.0
        breakdown["wall_xss_fixed"] = 5.0
    else:
        breakdown["wall_xss_fixed"] = 0.0

    if wall_patch_verification.get("broken_auth_fixed", False):
        wall_reward += 5.0
        breakdown["wall_broken_auth_fixed"] = 5.0
    else:
        breakdown["wall_broken_auth_fixed"] = 0.0

    if wall_patch_verification.get("functionality_preserved", False):
        wall_reward += 5.0
        breakdown["wall_functionality_preserved"] = 5.0
    else:
        breakdown["wall_functionality_preserved"] = 0.0

    if wall_patch_verification.get("new_vulns_introduced", False):
        wall_reward -= 5.0
        breakdown["wall_new_vulns_introduced"] = -5.0
    else:
        breakdown["wall_new_vulns_introduced"] = 0.0

    # ---- Cannon bypass phase ----
    if cannon_bypass_verification.get("real_vuln_found", False):
        cannon_reward += 15.0
        wall_reward   -= 5.0
        breakdown["bypass_succeeds_cannon"] = 15.0
        breakdown["bypass_succeeds_wall"]   = -5.0
        breakdown["bypass_fails_wall"]      = 0.0
    else:
        wall_reward += 5.0
        breakdown["bypass_succeeds_cannon"] = 0.0
        breakdown["bypass_succeeds_wall"]   = 0.0
        breakdown["bypass_fails_wall"]      = 5.0

    if cannon_bypass_verification.get("exploit_novel", False):
        cannon_reward += 2.0
        breakdown["bypass_exploit_novelty"] = 2.0
    else:
        breakdown["bypass_exploit_novelty"] = 0.0

    # ---- Clamp to achievable range ----
    cannon_reward = max(CANNON_MIN, min(CANNON_MAX, cannon_reward))
    wall_reward   = max(WALL_MIN,   min(WALL_MAX,   wall_reward))

    # ---- Normalize to [0, 1] ----
    cannon_span = CANNON_MAX - CANNON_MIN
    wall_span   = WALL_MAX   - WALL_MIN

    cannon_normalized = round((cannon_reward - CANNON_MIN) / cannon_span, 4)
    wall_normalized   = round((wall_reward   - WALL_MIN)   / wall_span,   4)

    cannon_normalized = max(0.0, min(1.0, cannon_normalized))
    wall_normalized   = max(0.0, min(1.0, wall_normalized))

    return {
        "cannon_total": cannon_normalized,
        "wall_total":   wall_normalized,
        "cannon_raw":   cannon_reward,
        "wall_raw":     wall_reward,
        "breakdown":    breakdown,
    }