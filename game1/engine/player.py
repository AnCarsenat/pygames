from .config import MAX_HP


class Player:
    def __init__(self, number, color, controls):
        self.number = number
        self.name = f"P{number}"
        self.color = color
        self.input = controls
        self.hp = MAX_HP

    @property
    def eliminated(self):
        return self.hp <= 0

    def lose_hp(self, amount=1):
        self.hp = max(0, self.hp - amount)

    def __repr__(self):
        return f"<{self.name} hp={self.hp}>"
