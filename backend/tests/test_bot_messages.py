"""Unit tests for the bot messages service."""
import pytest
from datetime import datetime, timedelta

from app.services.bot_messages import generate_fake_messages, BOT_MESSAGES


class TestGenerateFakeMessages:
    def test_returns_correct_count(self):
        msgs = generate_fake_messages(3, 55.75, 37.62)
        assert len(msgs) == 3

    def test_count_clamped_to_catalogue(self):
        # Requesting more messages than the catalogue has → clamped
        msgs = generate_fake_messages(len(BOT_MESSAGES) + 10, 55.75, 37.62)
        assert len(msgs) == len(BOT_MESSAGES)

    def test_zero_count_returns_empty(self):
        msgs = generate_fake_messages(0, 55.75, 37.62)
        assert msgs == []

    def test_message_texts_are_from_catalogue(self):
        msgs = generate_fake_messages(5, 55.75, 37.62)
        for msg in msgs:
            assert msg.text in BOT_MESSAGES

    def test_texts_are_unique(self):
        msgs = generate_fake_messages(5, 55.75, 37.62)
        texts = [m.text for m in msgs]
        assert len(texts) == len(set(texts))

    def test_timestamps_are_in_the_past(self):
        now = datetime.utcnow()
        msgs = generate_fake_messages(5, 55.75, 37.62)
        for msg in msgs:
            assert msg.created_at < now

    def test_timestamps_within_expected_range(self):
        now = datetime.utcnow()
        min_age = timedelta(minutes=5)
        max_age = timedelta(hours=2)
        msgs = generate_fake_messages(5, 55.75, 37.62)
        for msg in msgs:
            age = now - msg.created_at
            assert min_age <= age <= max_age + timedelta(seconds=5)  # small tolerance

    def test_sorted_newest_first(self):
        msgs = generate_fake_messages(5, 55.75, 37.62)
        for i in range(len(msgs) - 1):
            assert msgs[i].created_at >= msgs[i + 1].created_at

    def test_mystery_defaults(self):
        msgs = generate_fake_messages(3, 55.75, 37.62)
        for msg in msgs:
            assert msg.is_mystery is True
            assert msg.author_revealed is False
            assert msg.author_username is None

    def test_reaction_count_is_non_negative(self):
        msgs = generate_fake_messages(5, 55.75, 37.62)
        for msg in msgs:
            assert msg.reaction_count >= 0

    def test_user_has_reacted_is_false(self):
        msgs = generate_fake_messages(3, 55.75, 37.62)
        for msg in msgs:
            assert msg.user_has_reacted is False

    def test_ids_are_unique(self):
        msgs = generate_fake_messages(5, 55.75, 37.62)
        ids = [str(m.id) for m in msgs]
        assert len(ids) == len(set(ids))
