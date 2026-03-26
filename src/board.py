import numpy as np
from const import *
from square import Square
from piece import *
from move import Move

class Board:
    def __init__(self):
        self.squares = np.full((8, 8), 0, dtype = object)
        self.__create()
        self.__addPieces('white')
        self.__addPieces('black')
        self.lastMove = None
        self.promotionPending = False
        self.whiteKingPos = (7, 4)
        self.blackKingPos = (0, 4)
        self.enPassantTarget = None
        self.positionHistory = []
        self.halfmoveClock = 0
        self.currentTurn = 'white'
        self.moveLog = []

    def __create(self):
        for row in range(ROWS):
            for col in range(COLS):
                self.squares[row][col] = Square(row, col)

    def __addPieces(self, colour):
        pawnRow, otherRow = (1,0) if colour == 'black' else (6,7)
        # initialize pawns
        for col in range (COLS):
            self.squares[pawnRow][col] = Square(pawnRow, col, Pawn(colour))
        # initialize rooks
        self.squares[otherRow][0] = Square(otherRow, 0, Rook(colour))
        self.squares[otherRow][7] = Square(otherRow, 7, Rook(colour))
        # initialize knights
        self.squares[otherRow][1] = Square(otherRow, 1, Knight(colour))
        self.squares[otherRow][6] = Square(otherRow, 6, Knight(colour))
        # initialize bishops
        self.squares[otherRow][2] = Square(otherRow, 2, Bishop(colour))
        self.squares[otherRow][5] = Square(otherRow, 5, Bishop(colour))
        # initialize queen
        self.squares[otherRow][3] = Square(otherRow, 3, Queen(colour))
        # initialize king
        self.squares[otherRow][4] = Square(otherRow, 4, King(colour))

    def movePiece(self, piece, move):
        initialSquare = move.initialSquare
        destinationSquare = move.destinationSquare
        move.prevEnPassantTarget = self.enPassantTarget
        move.prevHalfmoveClock = self.halfmoveClock
        # save current state of the board for perft-test
        if move.isEnPassant:
            move.capturedPiece = self.squares[initialSquare.row][destinationSquare.col].piece
        else:
            move.capturedPiece = self.squares[destinationSquare.row][destinationSquare.col].piece

        self.squares[initialSquare.row][initialSquare.col].piece = None
        self.squares[destinationSquare.row][destinationSquare.col].piece = piece
        if isinstance(piece, King):
            if piece.colour == 'white':
                self.whiteKingPos = (destinationSquare.row, destinationSquare.col)
            else: self.blackKingPos = (destinationSquare.row, destinationSquare.col)

        # castling
        if move.isCastle:
            if destinationSquare.col == 6:
                rook = self.squares[destinationSquare.row][7].piece
                self.squares[destinationSquare.row][7].piece = None
                self.squares[destinationSquare.row][5].piece = rook

            elif destinationSquare.col == 2:
                rook = self.squares[destinationSquare.row][0].piece
                self.squares[destinationSquare.row][0].piece = None
                self.squares[destinationSquare.row][3].piece = rook

        # pawn promotion
        if isinstance(piece, Pawn):
            self.positionHistory = []  # after a pawn move its impossible to repeat a position
            promotionRow = 0 if piece.colour == 'white' else 7
            if destinationSquare.row == promotionRow:
                self.promotionPending = True

        # en passant
        if move.isEnPassant:
            self.squares[initialSquare.row][destinationSquare.col].piece = None
        if isinstance(piece, Pawn) and abs(destinationSquare.row - initialSquare.row) == 2:
            self.enPassantTarget = ((initialSquare.row + destinationSquare.row) // 2, initialSquare.col)
        else:
            self.enPassantTarget = None

        # increment halfmove clock if needed
        if isinstance(piece, Pawn) or move.capturedPiece is not None:
            self.halfmoveClock = 0
        else:
            self.halfmoveClock += 1

        piece.moved = True
        piece.clearMoves()
        self.lastMove = move
        nextTurn = 'white' if piece.colour == 'black' else 'black'
        positionHash = self.getPositionHash(nextTurn)
        self.positionHistory.append(positionHash)
        self.moveLog.append(move)
        if self.currentTurn == 'white':
            self.currentTurn = 'black'
        else:
            self.currentTurn = 'white'

    def isValidMove(self, piece, move):
        return move in piece.moves

    def isSafeMove(self, piece, move):
        startRow, startCol = move.initialSquare.row, move.initialSquare.col
        endRow, endCol = move.destinationSquare.row, move.destinationSquare.col
        oldKingPos = self.findKingPosistion(piece.colour)

        targetPiece = self.squares[endRow][endCol].piece
        self.squares[endRow][endCol].piece = piece
        self.squares[startRow][startCol].piece = None
        if isinstance(piece, King):
            if piece.colour == 'white':
                self.whiteKingPos = (endRow, endCol)
            else:
                self.blackKingPos = (endRow, endCol)
        # handle en passant
        if move.isEnPassant:
            capturedPawn = self.squares[startRow][endCol].piece
            self.squares[startRow][endCol].piece = None

        safe = not self.isInCheck(piece.colour)

        # rewind move
        self.squares[startRow][startCol].piece = piece
        self.squares[endRow][endCol].piece = targetPiece
        if piece.colour == 'white':
            self.whiteKingPos = oldKingPos
        else: self.blackKingPos = oldKingPos
        if move.isEnPassant:
            self.squares[startRow][endCol].piece = capturedPawn

        return safe

    def getPositionHash(self, nextTurn):
        # 1. Die Figuren-Konfiguration
        boardState = []
        for r in range(ROWS):
            for c in range(COLS):
                p = self.squares[r][c].piece
                if p:
                    boardState.append((r, c, p.colour, p.name))

        castlingRights = []
        for colour in ['white', 'black']:
            kingPos = self.whiteKingPos if colour == 'white' else self.blackKingPos
            king = self.squares[kingPos[0]][kingPos[1]].piece
            if king and not king.moved:
                rookRow = 0 if colour == 'black' else 7
                leftRook = self.squares[rookRow][0].piece
                if leftRook and not leftRook.moved:
                    castlingRights.append(f"{colour}_can_castle_queenside")
                rightRook = self.squares[rookRow][7].piece
                if rightRook and not rightRook.moved:
                    castlingRights.append(f"{colour}_can_castle_kingside")

        return (tuple(boardState), nextTurn, tuple(castlingRights), self.enPassantTarget)

    def isAttacked(self, row, col, colour):
        enemyColour = 'black' if colour == 'white' else 'white'

        for r in range(ROWS):
            for c in range(COLS):
                square = self.squares[r][c]
                if square.hasPiece() and square.piece.colour == enemyColour:
                    tempMoves = []
                    self.calculateMoves(square.piece, r, c, tempMoves, isTemporary = True, filterSafe = False)
                    for move in tempMoves:
                        if move.destinationSquare.row == row and move.destinationSquare.col == col:
                            return True
        return False

    def isInCheck(self, colour):
        kingPos = self.findKingPosistion(colour)
        return self.isAttacked(kingPos[0], kingPos[1], colour)

    def findKingPosistion(self, colour):
        return self.whiteKingPos if colour == 'white' else self.blackKingPos

    def completePromotion(self, row, col, colour, pieceType):
        classes = {"queen": Queen, "rook": Rook, "bishop": Bishop, "knight": Knight}
        self.squares[row][col] = Square(row, col, classes[pieceType](colour))
        self.promotionPending = False

    def checkCastlingMoves(self, piece, row, col, side):
        direction = 1 if side == 'kingSide' else -1
        rookCol = 7 if side == 'kingSide' else 0
        gapRange = range(1, 3) if side == 'kingSide' else range(1, 4)

        rook = self.squares[row][rookCol].piece
        if isinstance(rook, Rook):
            if not rook.moved:
                if all(not self.squares[row][col + (i * direction)].hasPiece() for i in gapRange):
                    if not self.isInCheck(piece.colour):
                        if all(not self.isAttacked(row, col + (i * direction), piece.colour) for i in range(1, 3)):
                            newMove = Move.createNewMove(row, col, row, col + 2 * direction, isCastle = True, isFirstMove = True)
                            piece.addMove(newMove)

    # perft-function to test if the move calculation works flawlessly
    def perft(self, depth):
        if depth == 0:
            return 1

        nodes = 0
        moves = self.getAllLegalMoves(self.currentTurn)

        for move in moves:
            movingPiece = self.squares[move.initialSquare.row][move.initialSquare.col].piece

            self.movePiece(movingPiece, move)

            nodes += self.perft(depth - 1)

            self.undoLastMove()

        return nodes

    # calculates every possible move for any piece of a specific colour
    def getAllLegalMoves(self, colour):
        allMoves = []
        for r in range(ROWS):
            for c in range(COLS):
                piece = self.squares[r][c].piece
                if piece and piece.colour == colour:
                    self.calculateMoves(piece, r, c, targetList = allMoves)

        return allMoves

    def undoLastMove(self):
        if len(self.moveLog) > 0:
            lastMove = self.moveLog.pop()
            self.undoMove(lastMove)

    def undoMove(self, move):
        startRow, startCol = move.initialSquare.row, move.initialSquare.col
        endRow, endCol = move.destinationSquare.row, move.destinationSquare.col

        piece = self.squares[endRow][endCol].piece
        self.squares[startRow][startCol].piece = piece
        self.squares[endRow][endCol].piece = None

        if move.capturedPiece:
            if move.isEnPassant:
                self.squares[startRow][endCol].piece = move.capturedPiece
            else:
                self.squares[endRow][endCol].piece = move.capturedPiece

        if isinstance(piece, King):
            if piece.colour == 'white':
                self.whiteKingPos = (startRow, startCol)
            else:
                self.blackKingPos = (startRow, startCol)

        self.enPassantTarget = move.prevEnPassantTarget
        self.halfmoveClock = move.prevHalfmoveClock
        if move.isFirstMove:
            piece.moved = False

        self.currentTurn = 'white' if self.currentTurn == 'black' else 'black'


    def calculateMoves(self, piece, row, col, tempMoves = None, isTemporary = False, filterSafe = True, targetList = None):

        if not isTemporary:
            piece.clearMoves()

        def addMove(move):
            if isTemporary:
                tempMoves.append(move)
            else:
                piece.addMove(move)

        def knightMoves():
            for dRow, dCol in KNIGHT_DIRECTIONS:
                possibleRow = row + dRow
                possibleCol = col + dCol
                if Square.isOnBoard(possibleRow, possibleCol):
                    if self.squares[possibleRow][possibleCol].isEmptyOrEnemy(piece.colour):
                        newMove = Move.createNewMove(row, col, possibleRow, possibleCol, isFirstMove = not piece.moved)
                        addMove(newMove)

        def pawnMoves():
            nextRow = row + piece.direction
             # standard (vertical) moves
            if not isTemporary:
                if Square.isOnBoard(nextRow, col) and self.squares[nextRow][col].isEmpty():
                    newMove = Move.createNewMove(row, col, nextRow, col, isFirstMove = not piece.moved)
                    addMove(newMove)
                    if not piece.moved:
                        possibleRow = row + piece.direction * 2
                        if self.squares[possibleRow][col].isEmpty():
                            newMove = Move.createNewMove(row, col, possibleRow, col, isFirstMove = not piece.moved)
                            addMove(newMove)
            # capturing (diagonal) moves
            for dCol in [1, -1]:
                possibleCol = col + dCol
                if Square.isOnBoard(nextRow, possibleCol):
                    if self.squares[nextRow][possibleCol].hasEnemyPiece(piece.colour):
                        newMove = Move.createNewMove(row, col, nextRow, possibleCol, isFirstMove = not piece.moved)
                        addMove(newMove)
                    # en passant moves
                    elif (nextRow, possibleCol) == self.enPassantTarget:
                        if (piece.colour == 'white' and row == 3) or (piece.colour == 'black' and row == 4):
                            newMove = Move.createNewMove(row, col, nextRow, possibleCol, isEnPassant = True)
                            addMove(newMove)

        def slidingMoves(directions, maxSteps):
            for dRow, dCol in directions:
                for i in range(1, maxSteps + 1):
                    possibleRow = row + dRow * i
                    possibleCol = col + dCol * i
                    if Square.isOnBoard(possibleRow, possibleCol):
                        if self.squares[possibleRow][possibleCol].isEmpty():
                            newMove = Move.createNewMove(row, col, possibleRow, possibleCol, isFirstMove = not piece.moved)
                            addMove(newMove)
                        elif self.squares[possibleRow][possibleCol].hasEnemyPiece(piece.colour):
                            newMove = Move.createNewMove(row, col, possibleRow, possibleCol, isFirstMove = not piece.moved)
                            addMove(newMove)
                            break
                        else: break
                    else: break

        def kingMoves():
            slidingMoves(KING_DIRECTIONS, maxSteps = 1)
            # castling
            if not isTemporary and not self.isInCheck(piece.colour) and not piece.moved:
                for side in ['kingSide', 'queenSide']:
                    self.checkCastlingMoves(piece, row, col, side)

        match piece:
            case Pawn(): pawnMoves()
            case Rook(): slidingMoves(ROOK_DIRECTIONS, 7)
            case Knight(): knightMoves()
            case Bishop(): slidingMoves(BISHOP_DIRECTIONS, 7)
            case Queen(): slidingMoves(QUEEN_DIRECTIONS, 7)
            case King(): kingMoves()
            case _: pass

        if not isTemporary:
            if filterSafe:
                piece.moves = [m for m in piece.moves if self.isSafeMove(piece, m)]
                for m in piece.moves:
                    if targetList is not None:
                        targetList.append(m)
        else:
            if filterSafe:
                tempMoves[:] = [m for m in tempMoves if self.isSafeMove(piece, m)]



