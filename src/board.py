from const import *
from square import Square
from piece import *
from move import Move
from zobrist import *

class Board:
    def __init__(self):
        self.squares = [[Square(r, c) for c in range(8)] for r in range(8)]
        self.__create()
        self.__addPieces('white')
        self.__addPieces('black')
        self.lastMove = None
        self.currentMove = None
        self.promotionPending = False
        self.whiteKingPos = (7, 4)
        self.blackKingPos = (0, 4)
        self.enPassantTarget = None
        self.positionHistory = []
        self.halfmoveClock = 0
        self.currentTurn = 'white'
        self.moveLog = []
        self.castleRights = [True, True, True, True]
        self.zobristHash = self.computePositionHash()


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
        # safe old hash for undo
        move.prevZobristHash = self.zobristHash

        initialSquare = move.initialSquare
        destinationSquare = move.destinationSquare
        self.currentMove = move
        move.prevEnPassantTarget = self.enPassantTarget
        move.prevHalfmoveClock = self.halfmoveClock
        move.prevCastleRights = self.castleRights[:]

        # save current state of the board for perft
        if move.isEnPassant:
            move.capturedPiece = self.squares[initialSquare.row][destinationSquare.col].piece
        else:
            move.capturedPiece = self.squares[destinationSquare.row][destinationSquare.col].piece

        # "delete" old position from zobrist hash
        pieceIndex = pieceZobristIndex(piece.colour, piece.name)
        fromIndex = initialSquare.row * 8 + initialSquare.col
        self.zobristHash ^= PIECEKEYS[pieceIndex][fromIndex]

        if move.capturedPiece and not move.isEnPassant:
            capturedIndex = pieceZobristIndex(move.capturedPiece.colour, move.capturedPiece.name)
            toIndex = destinationSquare.row * 8 + destinationSquare.col
            self.zobristHash ^= PIECEKEYS[capturedIndex][toIndex]

        if move.isEnPassant:
            enPassantRow = initialSquare.row
            enPassantCol = destinationSquare.col
            enPassantPiece = self.squares[enPassantRow][enPassantCol].piece
            enPassantIndex = pieceZobristIndex(enPassantPiece.colour, enPassantPiece.name)
            self.zobristHash ^= PIECEKEYS[enPassantIndex][enPassantRow * 8 + enPassantCol]

        for i in range(4):
            if self.castleRights[i]:
                self.zobristHash ^= CASTLEKEYS[i]

        if self.enPassantTarget is not None:
            self.zobristHash ^= ENPASSANTKEYS[self.enPassantTarget[1]]

        # execute move
        self.squares[initialSquare.row][initialSquare.col].piece = None
        self.squares[destinationSquare.row][destinationSquare.col].piece = piece

        if piece.name == 'king':
            if piece.colour == 'white':
                self.whiteKingPos = (destinationSquare.row, destinationSquare.col)
                self.castleRights[0] = False
                self.castleRights[1] = False
            else:
                self.blackKingPos = (destinationSquare.row, destinationSquare.col)
                self.castleRights[2] = False
                self.castleRights[3] = False

        # castling rights
        if initialSquare.row == 7 and initialSquare.col == 0 or destinationSquare.row == 7 and destinationSquare.col == 0:
            self.castleRights[1] = False
        if initialSquare.row == 7 and initialSquare.col == 7 or destinationSquare.row == 7 and destinationSquare.col == 7:
            self.castleRights[0] = False
        if initialSquare.row == 0 and initialSquare.col == 0 or destinationSquare.row == 0 and destinationSquare.col == 0:
            self.castleRights[3] = False
        if initialSquare.row == 0 and initialSquare.col == 7 or destinationSquare.row == 0 and destinationSquare.col == 7:
            self.castleRights[2] = False

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
        if piece.name == 'pawn':
            self.positionHistory = []  # after a pawn move its impossible to repeat a position
            promotionRow = 0 if piece.colour == 'white' else 7
            if destinationSquare.row == promotionRow:
                move.isPromotion = True
                move.promotionPiece = Queen(piece.colour)
                self.promotionPending = True

        # en passant
        if move.isEnPassant:
            self.squares[initialSquare.row][destinationSquare.col].piece = None
        if piece.name == 'pawn' and abs(destinationSquare.row - initialSquare.row) == 2:
            self.enPassantTarget = ((initialSquare.row + destinationSquare.row) // 2, initialSquare.col)
        else:
            self.enPassantTarget = None

        # increment halfmove clock if needed
        if piece.name == 'pawn' or move.capturedPiece is not None:
            self.halfmoveClock = 0
        else:
            self.halfmoveClock += 1

        piece.moved = True
        piece.clearMoves()
        self.lastMove = move
        self.moveLog.append(move)

        if self.currentTurn == 'white':
            self.currentTurn = 'black'
        else:
            self.currentTurn = 'white'

        # update zobrist hash
        toIndex = destinationSquare.row * 8 + destinationSquare.col
        newPiece = move.promotionPiece if move.isPromotion else piece
        newIndex = pieceZobristIndex(newPiece.colour, newPiece.name)
        self.zobristHash ^= PIECEKEYS[newIndex][toIndex]

        if move.isCastle:
            if destinationSquare.col == 6:
                rookFromIndex = destinationSquare.row * 8 + 7
                rookToIndex = initialSquare.row * 8 + 5
            else:
                rookFromIndex = initialSquare.row * 8 + 0
                rookToIndex = initialSquare.row * 8 + 3
            rookIndex = pieceZobristIndex(piece.colour, 'rook')
            self.zobristHash ^= PIECEKEYS[rookIndex][rookFromIndex]
            self.zobristHash ^= PIECEKEYS[rookIndex][rookToIndex]

        for i in range(4):
            if self.castleRights[i]:
                self.zobristHash ^= CASTLEKEYS[i]

        if self.enPassantTarget is not None:
            self.zobristHash ^= ENPASSANTKEYS[self.enPassantTarget[1]]

        self.zobristHash ^= SIDEKEY
        self.positionHistory.append(self.zobristHash)


    def isValidMove(self, piece, move):
        return move in piece.moves


    def isSafeMove(self, piece, move):
        startRow, startCol = move.initialSquare.row, move.initialSquare.col
        endRow, endCol = move.destinationSquare.row, move.destinationSquare.col
        oldKingPos = self.findKingPosistion(piece.colour)
        enemyColour = 'black' if piece.colour == 'white' else 'white'

        targetPiece = self.squares[endRow][endCol].piece
        self.squares[endRow][endCol].piece = piece
        self.squares[startRow][startCol].piece = None
        if piece.name == 'king':
            if piece.colour == 'white':
                self.whiteKingPos = (endRow, endCol)
            else:
                self.blackKingPos = (endRow, endCol)
        # handle en passant
        if move.isEnPassant:
            capturedPawn = self.squares[startRow][endCol].piece
            self.squares[startRow][endCol].piece = None

        kingPos = self.whiteKingPos if piece.colour == 'white' else self.blackKingPos

        safe = not self.isSquareAttacked(kingPos[0], kingPos[1], enemyColour)

        # rewind move
        self.squares[startRow][startCol].piece = piece
        self.squares[endRow][endCol].piece = targetPiece
        if piece.colour == 'white':
            self.whiteKingPos = oldKingPos
        else: self.blackKingPos = oldKingPos
        if move.isEnPassant:
            self.squares[startRow][endCol].piece = capturedPawn

        return safe


    def computePositionHash(self):
        hash = 0
        for r in range(8):
            for c in range(8):
                p = self.squares[r][c].piece
                if p:
                    hash ^= PIECEKEYS[pieceZobristIndex(p.colour, p.name)][squareIndex(r, c)]

        if self.currentTurn == 'black':
            hash ^= SIDEKEY

        for i in range(4):
            if self.castleRights[i]:
                hash ^= CASTLEKEYS[i]

        if self.enPassantTarget:
            hash ^= ENPASSANTKEYS[self.enPassantTarget[1]]
        return hash


    def isSquareAttacked(self, row, col, attackerColour):
        for dRow, dCol in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
            r, c = row + dRow, col + dCol
            if 0 <= r < 8 and 0 <= c < 8:
                p = self.squares[r][c].piece
                if p and p.name == 'knight' and p.colour == attackerColour:
                    return True

        pawnRow = row + (1 if attackerColour == 'white' else -1)
        for pawnCol in [col - 1, col + 1]:
            if 0 <= pawnRow < 8 and 0 <= pawnCol < 8:
                p = self.squares[pawnRow][pawnCol].piece
                if p and p.name == 'pawn' and p.colour == attackerColour:
                    return True

        for dRow in [-1, 0, 1]:
            for dCol in [-1, 0, 1]:
                if dRow == 0 and dCol == 0: continue
                r, c = row + dRow, col + dCol
                if 0 <= r < 8 and 0 <= c < 8:
                    p = self.squares[r][c].piece
                    if p and p.name == 'king' and p.colour == attackerColour:
                        return True

        slides = [ (((0, 1), (0, -1), (1, 0), (-1, 0)), 'rook'),
                   (((1, 1), (1, -1), (-1, 1), (-1, -1)), 'bishop') ]

        for directions, pieceType in slides:
            for dRow, dCol in directions:
                r, c = row + dRow, col + dCol
                while 0 <= r < 8 and 0 <= c < 8:
                    p = self.squares[r][c].piece
                    if p:
                        if p.colour == attackerColour and (p.name == pieceType or p.name == 'queen'):
                            return True
                        break
                    r += dRow
                    c += dCol

        return False


    def isInCheck(self, colour):
        kingPos = self.findKingPosistion(colour)
        enemyColour = 'white' if colour =='black' else 'black'
        return self.isSquareAttacked(kingPos[0], kingPos[1], enemyColour)


    def findKingPosistion(self, colour):
        return self.whiteKingPos if colour == 'white' else self.blackKingPos


    def completePromotion(self, row, col, colour, pieceType):
        classes = {"queen": Queen, "rook": Rook, "bishop": Bishop, "knight": Knight}
        self.squares[row][col] = Square(row, col, classes[pieceType](colour))
        self.currentMove.promotionPiece = self.squares[row][col].piece
        self.promotionPending = False


    def checkCastlingMoves(self, piece, row, col, side):
        direction = 1 if side == 'kingSide' else -1
        enemyColour = 'black' if piece.colour == 'white' else 'white'

        rookCol = 7 if side == 'kingSide' else 0
        gapRange = range(1, 3) if side == 'kingSide' else range(1, 4)
        transitRange = range(1, 3)

        rook = self.squares[row][rookCol].piece
        if rook and rook.name == 'rook':
            if not rook.moved:
                if all(not self.squares[row][col + (i * direction)].hasPiece() for i in gapRange):
                    if not self.isSquareAttacked(row, col, enemyColour):
                        if all(not self.isSquareAttacked(row, col + (i * direction), enemyColour) for i in transitRange):
                            newMove = Move.createNewMove(row, col, row, col + 2 * direction, isCastle=True, isFirstMove=True)
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

        if move.isPromotion:
            actualPiece = Pawn(piece.colour)
            actualPiece.moved = True
        else:
            actualPiece = piece

        self.squares[startRow][startCol].piece = actualPiece

        if move.capturedPiece:
            if move.isEnPassant:
                self.squares[startRow][endCol].piece = move.capturedPiece
            else:
                self.squares[endRow][endCol].piece = move.capturedPiece
        else:
            self.squares[endRow][endCol].piece = None

        if piece.name == 'king':
            if piece.colour == 'white':
                self.whiteKingPos = (startRow, startCol)
            else:
                self.blackKingPos = (startRow, startCol)

        self.enPassantTarget = move.prevEnPassantTarget
        self.halfmoveClock = move.prevHalfmoveClock
        if move.isFirstMove:
            piece.moved = False
        self.castleRights = move.prevCastleRights

        self.zobristHash = move.prevZobristHash
        if self.positionHistory:
            self.positionHistory.pop()

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



