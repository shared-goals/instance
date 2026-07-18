from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from shared_goals_instance.app import create_app


@pytest.fixture()
def client(tmp_path) -> Iterator[TestClient]:
    database_url = f"sqlite:///{tmp_path / 'shared_goals_test.db'}"
    app = create_app(database_url=database_url)
    with TestClient(app) as test_client:
        yield test_client
