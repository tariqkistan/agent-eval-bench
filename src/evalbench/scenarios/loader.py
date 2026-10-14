from pathlib import Path

import yaml

from evalbench.models import Scenario


def load_scenarios(yaml_path: str | Path) -> list[Scenario]:
    """Load scenarios from a YAML file and validate them with Pydantic."""
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    scenarios = [Scenario(**item) for item in data.get("scenarios", [])]
    if not scenarios:
        raise ValueError(f"No scenarios found in {path}")

    # Validate all IDs are unique
    ids = [s.id for s in scenarios]
    if len(ids) != len(set(ids)):
        raise ValueError("Scenario IDs must be unique")

    return scenarios
