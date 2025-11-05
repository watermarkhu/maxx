from maxx.collection import PathsCollection
from pathlib import Path


src = Path(__file__).parent.parent / "matlab_basics"

# Collect all MATLAB objects from a project
paths = PathsCollection([src], recursive=True)
