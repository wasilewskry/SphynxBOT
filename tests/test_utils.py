import datetime as dt

import pytest

from tests.conftest import MockException
from utils.misc import trim_by_paragraph, next_datetime, calculate_age, get_timezones, strptime, get_as_json, dm_open


class TestTrimByParagraph:
    def test_short(self):
        text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'
        assert trim_by_paragraph(text, fallback_length=100) == text

    def test_long(self):
        text = (
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit, '
            'sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
        )
        expected = (
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit, '
            'sed do eiusmod tempor incididunt ut labo...'
        )
        assert trim_by_paragraph(text, fallback_length=100) == expected

    def test_with_paragraphs(self):
        text = (
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'
            '\n'
            'Duis aute irure dolor in reprehenderit.'
            '\n'
            'In voluptate velit esse cillum dolore eu fugiat nulla pariatur. '
            'Excepteur sint occaecat cupidatat non proident, '
            'sunt in culpa qui officia deserunt mollit anim id est laborum.'
        )
        expected = (
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'
            '\n'
            'Duis aute irure dolor in reprehenderit.'
        )
        assert trim_by_paragraph(text, fallback_length=100) == expected


class TestNextDatetime:
    def test_same_day(self):
        current = dt.datetime(year=2000, month=6, day=6, hour=10, minute=10)
        expected = dt.datetime(year=2000, month=6, day=6, hour=12, minute=30)
        assert next_datetime(current, hour=12, minute=30) == expected

    def test_next_day(self):
        current = dt.datetime(year=2000, month=6, day=6, hour=10, minute=10)
        expected = dt.datetime(year=2000, month=6, day=7, hour=9, minute=30)
        assert next_datetime(current, hour=9, minute=30) == expected


class TestCalculateAge:
    born = dt.date(year=2000, month=6, day=6)

    def test_died_early(self):
        died = dt.datetime(year=2015, month=6, day=5)
        assert calculate_age(born=self.born, died=died) == 14

    def test_died_late(self):
        died = dt.datetime(year=2015, month=6, day=7)
        assert calculate_age(born=self.born, died=died) == 15


class TestGetTimezones:
    # Some systems can return an empty list, we check for that.

    def test_get_timezones(self):
        assert len(get_timezones()) > 0


class TestCustomStrptime:
    date_string = '2000-06-06 12:00'

    def test_with_time(self):
        assert strptime(self.date_string, '%Y-%m-%d %H:%M') == dt.datetime(year=2000, month=6, day=6, hour=12, minute=0)

    def test_without_time(self):
        assert strptime(self.date_string, '%Y-%m-%d %H:%M', no_time=True) == dt.date(year=2000, month=6, day=6)

    def test_garbled(self):
        assert strptime('asdasdsfg', '%Y-%m-%d %H:%M') is None


class TestGetAsJson:
    @pytest.mark.asyncio
    async def test_url(self, mocker):
        expected = {"mock_key": "mock_response"}
        mocker.patch('aiohttp.ClientSession.get').return_value.__aenter__.return_value.json.return_value = expected
        assert await get_as_json('mock_url') == expected


class TestDmOpen:
    @pytest.mark.asyncio
    async def test_is_open(self, mocker, mock_discord_user):
        mocker.patch('discord.HTTPException', MockException)
        mock_discord_user.send.side_effect = MockException(code=50006)
        assert await dm_open(mock_discord_user) is True

    @pytest.mark.asyncio
    async def test_is_closed(self, mocker, mock_discord_user):
        mocker.patch('discord.HTTPException', MockException)
        mock_discord_user.send.side_effect = MockException(code=50007)
        assert await dm_open(mock_discord_user) is False

    @pytest.mark.asyncio
    async def test_is_neither(self, mocker, mock_discord_user):
        mocker.patch('discord.HTTPException', MockException)
        mock_discord_user.send.side_effect = MockException(code=50008)
        with pytest.raises(MockException):
            await dm_open(mock_discord_user)
