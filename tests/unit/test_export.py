from pathlib import Path

import yaml

from app.main import app


def test_exported_contract_matches_application():
    assert yaml.safe_load(Path("openapi/openapi.yaml").read_text()) == app.openapi()
