import pytest
from discord.app_commands import Choice

from cogs.cinema.helpers import deduplicate_autocomplete_labels, prepare_production_autocomplete_choices
from cogs.cinema.models import Production


class TestHelpers:
    @pytest.fixture
    def choices(self):
        return [
            Choice(name='Taylor John Smith', value=1369329),
            Choice(name='Michael St. John Smith', value=77039),
            Choice(name='John Smith', value=151004),
            Choice(name='Timothy John Smith', value=1419122),
            Choice(name='John N. Smith', value=60295),
            Choice(name='John Smith', value=1291629),
            Choice(name='John Smith Kabashi', value=2374831),
            Choice(name='John Victor-Smith', value=29538),
            Choice(name='John Smith', value=6118),
            Choice(name='John Smithson', value=68542),
            Choice(name='John Smiley', value=1501158),
            Choice(name='John Smith', value=2607051),
            Choice(name='John A. Small', value=2725385),
            Choice(name='John Smallcombe', value=1486280),
            Choice(name='John Smythe', value=1505864),
            Choice(name='John Temple-Smith', value=38062),
            Choice(name='John T. Smith', value=930110),
            Choice(name='N. John Smith', value=72083),
            Choice(name='John Smith', value=1853052),
            Choice(name='John Smith', value=2603116),
        ]

    @pytest.fixture
    def deduplicated_choices(self):
        return [
            Choice(name='Taylor John Smith', value=1369329),
            Choice(name='Michael St. John Smith', value=77039),
            Choice(name='John Smith (1)', value=151004),
            Choice(name='Timothy John Smith', value=1419122),
            Choice(name='John N. Smith', value=60295),
            Choice(name='John Smith (2)', value=1291629),
            Choice(name='John Smith Kabashi', value=2374831),
            Choice(name='John Victor-Smith', value=29538),
            Choice(name='John Smith (3)', value=6118),
            Choice(name='John Smithson', value=68542),
            Choice(name='John Smiley', value=1501158),
            Choice(name='John Smith (4)', value=2607051),
            Choice(name='John A. Small', value=2725385),
            Choice(name='John Smallcombe', value=1486280),
            Choice(name='John Smythe', value=1505864),
            Choice(name='John Temple-Smith', value=38062),
            Choice(name='John T. Smith', value=930110),
            Choice(name='N. John Smith', value=72083),
            Choice(name='John Smith (5)', value=1853052),
            Choice(name='John Smith (6)', value=2603116),
        ]

    @pytest.fixture
    def candidates(self):
        return [
            Production(title='The Thing', id=2, popularity=4, release_date='2011-01-01'),
            Production(title='The Thing', id=4, popularity=2),
            Production(title='The Thing', id=1, popularity=5, release_date='1982-01-01'),
            Production(title='The Thing', id=5, popularity=1),
            Production(title='The Things', id=3, popularity=3, release_date='2021-01-01'),
            Production(title='The Thingy', id=6, popularity=0),
        ]

    @pytest.fixture
    def prepared_candidates(self):
        return [
            Choice(name='The Thing (1982)', value=1),
            Choice(name='The Thing (2011)', value=2),
            Choice(name='The Things (2021)', value=3),
            Choice(name='The Thing (1)', value=4),
            Choice(name='The Thing (2)', value=5),
            Choice(name='The Thingy', value=6),
        ]

    def test_deduplicate_autocomplete_labels(self, choices, deduplicated_choices):
        assert deduplicate_autocomplete_labels(choices) == deduplicated_choices

    def test_prepare_production_autocomplete_choices(self, candidates, prepared_candidates):
        assert prepare_production_autocomplete_choices(candidates) == prepared_candidates
