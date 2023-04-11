from unittest.mock import MagicMock

import discord
import pytest


@pytest.fixture
def mock_discord_user():
    return MagicMock(spec=discord.User)


class MockException(Exception):
    def __init__(self, **kwargs):
        self.code = kwargs.get('code')
