def build_wall_prompt(source_code: str, cannon_report: dict, stage: int) -> str:
    return f"""You are a Blue Team security engineer. Stage {stage}.
Red team found: {cannon_report}
Patch the vulnerability. Respond ONLY in this exact JSON format:
{{"agent":"wall","patched_code":"...full fixed file...","explanation":"..."}}

SOURCE CODE:
{source_code}"""
