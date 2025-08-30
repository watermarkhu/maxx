from pathlib import Path

import pytest

from maxx.collection import PathsCollection
from maxx.objects import Alias

submodules_dir = Path(__file__).parents[1] / "submodule"


@pytest.mark.parametrize(
    "matlab_path, recursive",
    [
        ([submodules_dir / "advanced-logger" / "advancedLogger"], False),
        ([submodules_dir / "gnu-octave-statistics"], True),
        ([submodules_dir / "OpenTelemetry-MATLAB"], True),
    ],
)
def test_submodule_directory(matlab_path, recursive):
    # Example assertion: check that the directory exists and is not empty
    collection = PathsCollection(matlab_path, recursive=recursive)
    for name, object in collection.members.items():
        if isinstance(object, Alias):
            assert object.target is not None, f"Alias '{name}' has no target"
