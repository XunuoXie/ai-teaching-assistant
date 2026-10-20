
import re

FORBIDDEN_MODULES = [
    'os', 'subprocess', 'shutil', 'socket',
    'requests', 'urllib', 'importlib', '__builtins__'
]
FORBIDDEN_KEYWORDS = ['exec', 'eval', 'compile']


def is_safe_code(code: str) -> bool:
    code_lower = code.lower()
    
    for mod in FORBIDDEN_MODULES:
        if re.search(rf'\bimport\s+{mod}\b', code) or \
           re.search(rf'\bfrom\s+{mod}\s+import\b', code):
            return False
    
    for kw in FORBIDDEN_KEYWORDS:
        if re.search(rf'\b{re.escape(kw)}\b', code_lower):
            return False
    
    if '__import__' in code:
        for mod in FORBIDDEN_MODULES:
            if f"__import__('{mod}')" in code or f'__import__("{mod}")' in code:
                return False
    
    if 'open(' in code and ('/etc/' in code or 'C:\\windows' in code or '\\windows\\' in code):
        return False
    
    return True
