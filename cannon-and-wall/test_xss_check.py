def xss_fixed_check(code):
    return (
        "html.escape" in code or "escape(" in code or
        "Markup.escape" in code or "autoescape" in code
    ) and "{comment}" not in code

good = '''import html
safe = html.escape(comment)
return f"<html>{safe}</html>"'''
bad1 = '''import html
return f"<html>{comment}</html>"'''   # escape present, raw var still there
bad2 = 'return f"<html>{comment}</html>"'                 # nothing fixed

assert xss_fixed_check(good) == True,  "FAIL: good patch rejected"
assert xss_fixed_check(bad1) == False, "FAIL: bad1 accepted — raw {comment} still present"
assert xss_fixed_check(bad2) == False, "FAIL: bad2 accepted — no escape at all"
print("✅ XSS check passed")
