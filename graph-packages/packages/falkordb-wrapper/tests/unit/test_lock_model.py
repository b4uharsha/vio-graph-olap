"""Tests for lock state model."""

from datetime import datetime

from wrapper.models.lock import LockState, lock_info_from_state


class TestLockState:
    def test_to_api_dict(self):
        state = LockState(
            execution_id="exec-1",
            holder_id="user-1",
            holder_username="alice",
            algorithm_name="pagerank",
            algorithm_type="cypher",
            acquired_at=datetime(2026, 1, 1, 12, 0, 0),
        )
        d = state.to_api_dict()
        assert d["execution_id"] == "exec-1"
        assert d["holder_username"] == "alice"
        assert "2026-01-01" in d["acquired_at"]

    def test_frozen(self):
        state = LockState(
            execution_id="exec-1",
            holder_id="user-1",
            holder_username="alice",
            algorithm_name="pagerank",
            algorithm_type="cypher",
            acquired_at=datetime(2026, 1, 1),
        )
        import pytest
        with pytest.raises(Exception):
            state.execution_id = "changed"


class TestLockInfoFromState:
    def test_none_returns_unlocked(self):
        info = lock_info_from_state(None)
        assert info.locked is False

    def test_state_returns_locked(self):
        state = LockState(
            execution_id="exec-1",
            holder_id="user-1",
            holder_username="alice",
            algorithm_name="pagerank",
            algorithm_type="cypher",
            acquired_at=datetime(2026, 1, 1),
        )
        info = lock_info_from_state(state)
        assert info.locked is True
        assert info.execution_id == "exec-1"
