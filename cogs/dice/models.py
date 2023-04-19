import random
from collections import Counter


class Dice:
    """Represents a set of dice that can be rolled."""

    def __init__(self, dice_count: int, face_count: int):
        if dice_count < 1 or face_count < 1:
            raise ValueError('Dice and face count should both be higher than 0.')
        self.dice_count = dice_count
        self.face_count = face_count
        self.most_recent_roll = Counter()

    def roll(self) -> Counter[int, int]:
        """Rolls the dice and tallies the results."""
        self.most_recent_roll = Counter([random.randint(1, self.face_count) for _ in range(self.dice_count)])
        return self.most_recent_roll

    def sum(self) -> int:
        """Returns the sum of the faces from the last roll."""
        return sum([count * value for value, count in self.most_recent_roll.items()])

    def successes(self, threshold: int) -> int:
        """Returns the number of results greater than or equal to the threshold."""
        return sum([count for value, count in self.most_recent_roll.items() if value >= threshold])

    def failures(self, threshold: int) -> int:
        """Returns the number of results lesser than or equal to the threshold."""
        return sum([count for value, count in self.most_recent_roll.items() if value <= threshold])
