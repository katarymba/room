"""Unit tests for mystery mode logic (room_service)."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.room_service import check_author_reveal, _has_mutual_reaction, _uuid_in_list


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_message(*, user_id=None, created_at=None, revealed_to=None, is_mystery=True):
    msg = MagicMock()
    msg.id = uuid4()
    msg.user_id = user_id or uuid4()
    msg.created_at = created_at or datetime.utcnow()
    msg.revealed_to = revealed_to or []
    msg.is_mystery = is_mystery
    msg.user = None
    return msg


def _make_db(*, user_liked_message=False, author_liked_back=False):
    """Return a mock DB session that simulates reaction queries."""
    db = MagicMock()

    def query_side_effect(model):
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        # first() controls whether user liked / author liked back
        q.first.return_value = MagicMock() if user_liked_message else None
        return q

    db.query.side_effect = query_side_effect
    return db


# ── _uuid_in_list ─────────────────────────────────────────────────────────────


class TestUuidInList:
    def test_present(self):
        uid = uuid4()
        assert _uuid_in_list(uid, [uid]) is True

    def test_absent(self):
        assert _uuid_in_list(uuid4(), [uuid4(), uuid4()]) is False

    def test_empty(self):
        assert _uuid_in_list(uuid4(), []) is False

    def test_string_match(self):
        uid = uuid4()
        assert _uuid_in_list(uid, [str(uid)]) is True


# ── check_author_reveal ───────────────────────────────────────────────────────


class TestCheckAuthorReveal:
    def test_own_message_is_always_revealed(self):
        user_id = uuid4()
        msg = _make_message(user_id=user_id)
        db = _make_db()
        assert check_author_reveal(db, msg, user_id) is True

    def test_already_in_revealed_to(self):
        viewer_id = uuid4()
        msg = _make_message(revealed_to=[viewer_id])
        db = _make_db()
        assert check_author_reveal(db, msg, viewer_id) is True

    def test_old_message_is_revealed(self):
        viewer_id = uuid4()
        msg = _make_message(created_at=datetime.utcnow() - timedelta(hours=25))
        db = _make_db()
        assert check_author_reveal(db, msg, viewer_id) is True

    def test_new_message_without_mutual_reaction_not_revealed(self):
        viewer_id = uuid4()
        msg = _make_message(created_at=datetime.utcnow() - timedelta(hours=1))
        db = _make_db(user_liked_message=False)
        assert check_author_reveal(db, msg, viewer_id) is False

    def test_one_sided_like_not_revealed(self):
        """User liked the message but author hasn't liked anything back."""
        viewer_id = uuid4()
        msg = _make_message(created_at=datetime.utcnow() - timedelta(hours=1))

        db = MagicMock()
        call_count = [0]

        def query_side_effect(model):
            q = MagicMock()
            q.filter.return_value = q
            q.join.return_value = q
            call_count[0] += 1
            # First call: user liked → True; Second call: author liked back → False
            q.first.return_value = MagicMock() if call_count[0] == 1 else None
            return q

        db.query.side_effect = query_side_effect
        assert check_author_reveal(db, msg, viewer_id) is False
