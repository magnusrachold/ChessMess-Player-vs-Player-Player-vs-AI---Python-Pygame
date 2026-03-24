from square import Square

class Move:
    def __init__(self, initialSquare, destinationSquare, isCastle = False, isEnPassant = False):
        self.initialSquare = initialSquare
        self.destinationSquare = destinationSquare
        self.isCastle = isCastle
        self.isEnPassant = isEnPassant

    @staticmethod
    def createNewMove(initialRow, initialCol, destinationRow, destinationCol, isCastle = False, isEnPassant = False):
        initialSquare = Square(initialRow, initialCol)
        destinationSquare = Square(destinationRow, destinationCol)
        return Move(initialSquare, destinationSquare, isCastle, isEnPassant)

    def __eq__(self, other):
        return self.initialSquare == other.initialSquare and self.destinationSquare == other.destinationSquare