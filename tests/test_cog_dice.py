from collections import Counter

import pytest

from cogs.dice.models import Dice


class TestModelsDice:
    def test_init(self):
        with pytest.raises(ValueError):
            Dice(-1, 0)

    def test_roll(self, mocker):
        mocker.patch('random.randint').return_value = 5
        dice = Dice(3, 10)
        expected = Counter({5: 3})
        assert dice.roll() == expected
        assert dice.most_recent_roll == expected

    def test_sum(self):
        dice = Dice(3, 6)
        dice.most_recent_roll = Counter({3: 3})
        expected = 9
        assert dice.sum() == expected

    def test_successes(self):
        dice = Dice(5, 5)
        dice.most_recent_roll = Counter({5: 2, 3: 1, 1: 1})
        assert dice.successes(3) == 3

    def test_failures(self):
        dice = Dice(5, 5)
        dice.most_recent_roll = Counter({5: 2, 3: 1, 1: 1})
        assert dice.failures(3) == 2
