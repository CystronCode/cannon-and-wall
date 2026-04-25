def build_cannon_prompt(source_code: str, stage: int, round: int) -> str:
    return f"""You are a Red Team security analyst. Stage {stage}, Round {round}.
Analyze this source code and find ONE vulnerability.
Respond ONLY in this exact JSON format:
{{"agent":"cannon","vuln_type":"sqli|xss|broken_auth","line_number":0,"explanation":"...","proof_of_concept":"..."}}

SOURCE CODE:
{source_code}"""
