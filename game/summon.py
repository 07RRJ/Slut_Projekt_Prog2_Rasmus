class player:
    HP: int = 10
    BLOCK: int = 0
    ATTACK: int = 0
    STR: int = 1
    BOOST: int = 1

    def GetAttack(self):
        self.ATTACK = self.STR * self.BOOST

    def Hurt():
        print("hp")

    def ShieldDmg():
        print("shield")

    def TakeDmg(self, DMG):
        if DMG:
            if (self.BLOCK - DMG) > 0:
                self.HP -= self.BLOCK - DMG
                self.Hurt()
            else:
                self.BLOCK -= DMG
                self.ShieldDmg()

    def Attack(self, enemy):
        self.GetAttack()
        enemy.TakeDmg(self.ATTACK)

class Player(player):
    def __init__(self):
        super().__init__()