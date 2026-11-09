"""Import projects/carrie-ep01/build_long2.py (for L2.find / L2.WS) robustly.

scripts/podcast.py is being edited by another specialist and can be mid-edit (syntax error). build_long2 only needs
podcast.bare() at import time, so if the real module fails to import we register a tiny stand-in with the identical
bare() definition (re.sub(r"[^\\w%'-]", "", s).lower()) and import build_long2 unchanged.
"""
import os, re, sys, types

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
EP = os.path.join(ROOT, "projects", "carrie-ep01")
for p in (EP, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
argv = sys.argv[:]
try:
    import podcast  # noqa: F401
except SyntaxError:
    shim = types.ModuleType("podcast")
    shim.bare = lambda s: re.sub(r"[^\w%'-]", "", s).lower()
    shim.tighten = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("podcast.py unavailable"))
    sys.modules["podcast"] = shim
import build_long2 as L2  # noqa: E402
sys.argv = argv
