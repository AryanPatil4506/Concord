import os
import sys

# the engine modules (concord_sim, storyboard) live one level up
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
