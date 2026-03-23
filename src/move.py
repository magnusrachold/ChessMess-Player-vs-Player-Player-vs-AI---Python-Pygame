from square import Square

class Move:
    def __init__(self, initialSquare, destinationSquare, isCastle = False):
        self.initialSquare = initialSquare
        self.destinationSquare = destinationSquare
        self.isCastle = isCastle

    @staticmethod
    def createNewMove(initialRow, initialCol, destinationRow, destinationCol, isCastle = False):
        initialSquare = Square(initialRow, initialCol)
        destinationSquare = Square(destinationRow, destinationCol)
        return Move(initialSquare, destinationSquare, isCastle)

    def __eq__(self, other):
        return self.initialSquare == other.initialSquare and self.destinationSquare == other.destinationSquare