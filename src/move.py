from square import Square

class Move:
    def __init__(self, initialSquare, destinationSquare, isCastle = False, isEnPassant = False, isFirstMove = False, isPromotion = False):
        self.initialSquare = initialSquare
        self.destinationSquare = destinationSquare
        self.isCastle = isCastle
        self.isEnPassant = isEnPassant
        self.isPromotion = isPromotion
        self.capturedPiece = None
        self.promotionPiece = None
        self.prevEnPassantTarget = None
        self.prevHalfmoveClock = 0
        self.isFirstMove = isFirstMove
        self.prevZobristHash = None
        self.prevCastleRights = None
        self.prevMovedState = False

    @staticmethod
    def createNewMove(initialRow, initialCol, destinationRow, destinationCol, isCastle = False, isEnPassant = False, isFirstMove = False, isPromotion = False):
        initialSquare = (initialRow, initialCol)
        destinationSquare = (destinationRow, destinationCol)
        return Move(initialSquare, destinationSquare, isCastle, isEnPassant, isFirstMove, isPromotion)

    def __eq__(self, other):
        return self.initialSquare == other.initialSquare and self.destinationSquare == other.destinationSquare

    def __str__(self):
        return f"{self.getChessNotation(self.initialSquare)}->{self.getChessNotation(self.destinationSquare)}"

    def __repr__(self):
        return self.__str__()

    def getChessNotation(self, square):
        ranksToRows = {"8": 0, "7": 1, "6": 2, "5": 3, "4": 4, "3": 5, "2": 6, "1": 7}
        rowsToRanks = {v: k for k, v in ranksToRows.items()}
        filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
        colsToFiles = {v: k for k, v in filesToCols.items()}

        return colsToFiles[square[1]] + rowsToRanks[square[0]]