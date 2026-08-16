# Swarm multi-agent package
import os
import sys

# Inject shims directory into sys.path
shims_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shims")
if shims_dir not in sys.path:
    sys.path.insert(0, shims_dir)
