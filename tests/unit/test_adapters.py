from unittest.mock import Mock
import time

import pytest
from redis.exceptions import ConnectionError

from app.adapters.redis import RedisAdapter
from app.config.settings import Settings
from app.errors import ApiError
from app.services.cursors import CursorCodec


def test_redis_expired_and_missing_are_not_dependency_errors():
    adapter = RedisAdapter(Settings(_env_file=None))
    adapter.client = Mock()
    pipe = adapter.client.pipeline.return_value.__enter__ = Mock()
    transaction = Mock()
    pipe.return_value = transaction
    adapter.client.pipeline.return_value.__exit__ = Mock(return_value=False)
    transaction.hgetall.return_value.ttl.return_value.execute.return_value = [{}, -2]
    assert adapter.session("gone") is None
    transaction.hgetall.return_value.ttl.return_value.execute.side_effect = ConnectionError("secret")
    with pytest.raises(ApiError) as error:
        adapter.session("gone")
    assert error.value.status == 503
    assert "secret" not in str(error.value)


def test_cursor_expiration_and_tamper(monkeypatch):
    codec = CursorCodec("test-key")
    token = codec.encode(b"paging-state", ["P001"])
    assert codec.decode(token, ["P001"]) == b"paging-state"
    with pytest.raises(ApiError):
        codec.decode(token, ["P002"])
    with pytest.raises(ApiError):
        codec.decode("A"+token[1:], ["P001"])
    now = time.time()
    monkeypatch.setattr(time, "time", lambda: now+3601)
    with pytest.raises(ApiError):
        codec.decode(token, ["P001"])
