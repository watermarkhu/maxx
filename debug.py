from pathlib import Path

from maxx.collection import PathsCollection

src = Path(__file__).parent / "submodule" / "OpenTelemetry-MATLAB"

# Collect all MATLAB objects from a project
paths = PathsCollection([src], recursive=True)
