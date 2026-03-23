
class Square:
    def __init__(self, row, col, piece = None):
        self.row = row
        self.col = col
        self.piece = piece

    def hasPiece(self):
        return self.piece != None

    @staticmethod
    def isOnBoard(row, col):
        if row < 0 or row > 7 or col < 0 or col > 7:
                return False
        return True

    def isEmptyOrEnemy(self, colour):
        return self.isEmpty() or self.hasEnemyPiece(colour)
    def isEmpty(self):
        return not self.hasPiece()
    def hasAllyPiece(self, colour):
        return self.hasPiece() and self.piece.colour == colour
    def hasEnemyPiece(self, colour):
        return self.hasPiece() and self.piece.colour != colour

    def __eq__(self, other):
        return self.row == other.row and self.col == other.col