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

        initialRow, initialCol = move.initialSquare[0], move.initialSquare[1]
        destinationRow, destinationCol = move.destinationSquare[0], move.destinationSquare[1]
        self.currentMove = move
        move.prevEnPassantTarget = self.enPassantTarget
        move.prevHalfmoveClock = self.halfmoveClock
        move.prevCastleRights = self.castleRights[:]
        move.prevMovedState = piece.moved

        # save current state of the board for perft
        if move.isEnPassant:
            move.capturedPiece = self.squares[initialRow][destinationCol].piece
        else:
            move.capturedPiece = self.squares[destinationRow][destinationCol].piece

        # "delete" old position from zobrist hash
        pieceIndex = pieceZobristIndex(piece.colour, piece.name)
        fromIndex = initialRow * 8 + initialCol
        self.zobristHash ^= PIECEKEYS[pieceIndex][fromIndex]

        if move.capturedPiece and not move.isEnPassant:
            capturedIndex = pieceZobristIndex(move.capturedPiece.colour, move.capturedPiece.name)
            toIndex = destinationRow * 8 + destinationCol
            self.zobristHash ^= PIECEKEYS[capturedIndex][toIndex]

        if move.isEnPassant:
            enPassantRow = initialRow
            enPassantCol = destinationCol
            enPassantPiece = self.squares[enPassantRow][enPassantCol].piece
            enPassantIndex = pieceZobristIndex(enPassantPiece.colour, enPassantPiece.name)
            self.zobristHash ^= PIECEKEYS[enPassantIndex][enPassantRow * 8 + enPassantCol]

        for i in range(4):
            if self.castleRights[i]:
                self.zobristHash ^= CASTLEKEYS[i]

        if self.enPassantTarget is not None:
            self.zobristHash ^= ENPASSANTKEYS[self.enPassantTarget[1]]

        # execute move
        self.squares[initialRow][initialCol].piece = None
        self.squares[destinationRow][destinationCol].piece = piece

        if piece.name == 'king':
            if piece.colour == 'white':
                self.whiteKingPos = (destinationRow, destinationCol)
                self.castleRights[0] = False
                self.castleRights[1] = False
            else:
                self.blackKingPos = (destinationRow, destinationCol)
                self.castleRights[2] = False
                self.castleRights[3] = False

        # castling rights
        if initialRow == 7 and initialCol == 0 or destinationRow == 7 and destinationCol == 0:
            self.castleRights[1] = False
        if initialRow == 7 and initialCol == 7 or destinationRow == 7 and destinationCol == 7:
            self.castleRights[0] = False
        if initialRow == 0 and initialCol == 0 or destinationRow == 0 and destinationCol == 0:
            self.castleRights[3] = False
        if initialRow == 0 and initialCol == 7 or destinationRow == 0 and destinationCol == 7:
            self.castleRights[2] = False

        # castling
        if move.isCastle:
            if destinationCol == 6:
                rook = self.squares[destinationRow][7].piece
                self.squares[destinationRow][7].piece = None
                self.squares[destinationRow][5].piece = rook

            elif destinationCol == 2:
                rook = self.squares[destinationRow][0].piece
                self.squares[destinationRow][0].piece = None
                self.squares[destinationRow][3].piece = rook

        # pawn promotion
        if piece.name == 'pawn':
            self.positionHistory = []  # after a pawn move its impossible to repeat a position
            promotionRow = 0 if piece.colour == 'white' else 7
            if destinationRow == promotionRow:
                move.isPromotion = True
                self.squares[destinationRow][destinationCol].piece = move.promotionPiece
                self.promotionPending = True

        # en passant
        if move.isEnPassant:
            self.squares[initialRow][destinationCol].piece = None
        if piece.name == 'pawn' and abs(destinationRow - initialRow) == 2:
            self.enPassantTarget = ((initialRow + destinationRow) // 2, initialCol)
        else:
            self.enPassantTarget = None

        # increment halfmove clock if needed
        if piece.name == 'pawn' or move.capturedPiece:
            self.halfmoveClock = 0
        else:
            self.halfmoveClock += 1

        piece.moved = True
        piece.clearMoves()
        self.lastMove = move
        self.moveLog.append(move)

        self.currentTurn = 'white' if self.currentTurn == 'black' else 'black'

        # update zobrist hash
        toIndex = destinationRow * 8 + destinationCol
        newPiece = move.promotionPiece if move.isPromotion else piece
        newIndex = pieceZobristIndex(newPiece.colour, newPiece.name)
        self.zobristHash ^= PIECEKEYS[newIndex][toIndex]

        if move.isCastle:
            if destinationCol == 6:
                rookFromIndex = destinationRow * 8 + 7
                rookToIndex = initialRow * 8 + 5
            else:
                rookFromIndex = initialRow * 8 + 0
                rookToIndex = initialRow * 8 + 3
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
        startRow, startCol = move.initialSquare[0], move.initialSquare[1]
        endRow, endCol = move.destinationSquare[0], move.destinationSquare[1]
        oldKingPos = self.findKingPosistion(piece.colour)

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


    def computePositionHash(self):
        hash = 0
        for r in range(ROWS):
            for c in range(COLS):
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

        if piece.colour == 'white':
            if side == 'kingSide' and not self.castleRights[0]: return
            if side == 'queenSide' and not self.castleRights[1]: return
        else:
            if side == 'kingSide' and not self.castleRights[2]: return
            if side == 'queenSide' and not self.castleRights[3]: return

        rook = self.squares[row][rookCol].piece
        if rook and rook.name == 'rook':
            if not rook.moved:
                if all(not self.squares[row][col + (i * direction)].hasPiece() for i in gapRange):
                    if not self.isSquareAttacked(row, col, enemyColour):
                        if all(not self.isSquareAttacked(row, col + (i * direction), enemyColour) for i in transitRange):
                            return Move.createNewMove(row, col, row, col + 2 * direction, isCastle=True, isFirstMove=True)
        return None


    def perft(self, depth):
        """ perft-function to test if the move calculation works flawlessly """
        if depth == 0:
            return 1

        nodes = 0
        moves = self.getAllLegalMoves(self.currentTurn)

        for move in moves:
            movingPiece = self.squares[move.initialSquare[0]][move.initialSquare[1]].piece

            self.movePiece(movingPiece, move)

            nodes += self.perft(depth - 1)

            self.undoLastMove()

        return nodes



    def getAllLegalMoves(self, colour):
        """ calculates every possible move for any piece of a specific colour """
        allMoves = []
        for r in range(ROWS):
            for c in range(COLS):
                piece = self.squares[r][c].piece
                if piece and piece.colour == colour:
                    legalMoves = self.calculateMoves(piece, r, c)
                    allMoves.extend(legalMoves)

        return allMoves


    def undoLastMove(self):
        if len(self.moveLog) > 0:
            lastMove = self.moveLog.pop()
            self.undoMove(lastMove)


    def undoMove(self, move):
        startRow, startCol = move.initialSquare[0], move.initialSquare[1]
        endRow, endCol = move.destinationSquare[0], move.destinationSquare[1]

        piece = self.squares[endRow][endCol].piece

        if move.isPromotion:
            actualPiece = Pawn(piece.colour)
        else:
            actualPiece = piece

        self.squares[startRow][startCol].piece = actualPiece
        self.squares[endRow][endCol].piece = None

        if move.capturedPiece:
            if move.isEnPassant:
                self.squares[startRow][endCol].piece = move.capturedPiece
            else:
                self.squares[endRow][endCol].piece = move.capturedPiece

        if piece.name == 'king':
            if piece.colour == 'white':
                self.whiteKingPos = (startRow, startCol)
            else:
                self.blackKingPos = (startRow, startCol)

        if move.isCastle:
            if endCol == 6:
                rook = self.squares[endRow][5].piece
                self.squares[endRow][5].piece = None
                self.squares[endRow][7].piece = rook
                rook.moved = False
            elif endCol == 2:
                rook = self.squares[endRow][3].piece
                self.squares[endRow][3].piece = None
                self.squares[endRow][0].piece = rook
                rook.moved = False

        self.enPassantTarget = move.prevEnPassantTarget
        self.halfmoveClock = move.prevHalfmoveClock
        actualPiece.moved = move.prevMovedState
        self.castleRights = move.prevCastleRights

        self.zobristHash = move.prevZobristHash
        if self.positionHistory:
            self.positionHistory.pop()

        self.currentTurn = 'white' if self.currentTurn == 'black' else 'black'


    def calculateMoves(self, piece, row, col, filterSafe = True):
        piece.clearMoves()
        moves = []

        def addMove(move):
            moves.append(move)

        def knightMoves():
            for dRow, dCol in KNIGHT_DIRECTIONS:
                possibleRow = row + dRow
                possibleCol = col + dCol
                if Square.isOnBoard(possibleRow, possibleCol):
                    if self.squares[possibleRow][possibleCol].isEmptyOrEnemy(piece.colour):
                        newMove = Move.createNewMove(row, col, possibleRow, possibleCol, isFirstMove = not piece.moved)
                        addMove(newMove)

        def pawnMoves():
            promotionRow = 0 if piece.colour == 'white' else 7
            nextRow = row + piece.direction

             # standard (vertical) moves
            if Square.isOnBoard(nextRow, col) and self.squares[nextRow][col].isEmpty():
                if nextRow == promotionRow:
                    for promotionPiece in [Queen(piece.colour), Rook(piece.colour), Bishop(piece.colour), Knight(piece.colour)]:
                        newMove = Move.createNewMove(row, col, nextRow, col, isPromotion = True)
                        newMove.promotionPiece = promotionPiece
                        addMove(newMove)
                else:
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
                        if nextRow == promotionRow:
                            for promotionPiece in [Queen(piece.colour), Rook(piece.colour), Bishop(piece.colour), Knight(piece.colour)]:
                                newMove = Move.createNewMove(row, col, nextRow, possibleCol, isPromotion = True)
                                newMove.promotionPiece = promotionPiece
                                addMove(newMove)
                        else:
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
            if not self.isInCheck(piece.colour) and not piece.moved:
                for side in ['kingSide', 'queenSide']:
                   castlingMove = self.checkCastlingMoves(piece, row, col, side)
                   if castlingMove:
                        addMove(castlingMove)

        match piece:
            case Pawn(): pawnMoves()
            case Rook(): slidingMoves(ROOK_DIRECTIONS, 7)
            case Knight(): knightMoves()
            case Bishop(): slidingMoves(BISHOP_DIRECTIONS, 7)
            case Queen(): slidingMoves(QUEEN_DIRECTIONS, 7)
            case King(): kingMoves()
            case _: pass

        if filterSafe:
            moves = [m for m in moves if self.isSafeMove(piece, m)]

        piece.moves.extend(moves)

        return moves


    @classmethod
    def boardStateFromFen(cls, fen: str) -> 'Board':
        """ reads a FEN (standard representation of a board state) and creates a board in that exact state """
        board = cls.__new__(cls)

        board.squares = [[Square(r, c) for c in range(8)] for r in range(8)]
        board.__create()
        board.lastMove = None
        board.currentMove = None
        board.promotionPending = False
        board.enPassantTarget = None
        board.positionHistory = []
        board.halfmoveClock = 0
        board.moveLog = []
        board.castleRights = [False, False, False, False]
        board.whiteKingPos = None
        board.blackKingPos = None

        parts = fen.strip().split()
        pieceRows = parts[0]
        turn = parts[1] if len(parts) > 1 else 'w'
        castling = parts[2] if len(parts) > 2 else '-'
        enPassant = parts[3] if len(parts) > 3 else '-'
        halfmove = parts[4] if len(parts) > 4 else '0'

        pieceMap = {
            'P': Pawn, 'p': Pawn,
            'R': Rook, 'r': Rook,
            'N': Knight, 'n': Knight,
            'B': Bishop, 'b': Bishop,
            'Q': Queen, 'q': Queen,
            'K': King, 'k': King,
        }

        for row, rankString in enumerate(pieceRows.split('/')):
            col = 0
            for c in rankString:
                if c.isdigit():
                    col += int(c)
                else:
                    colour = 'white' if c.isupper() else 'black'
                    piece = pieceMap[c](colour)
                    piece.moved = True
                    board.squares[row][col].piece = piece
                    if c == 'K':
                        board.whiteKingPos = (row, col)
                    elif c == 'k':
                        board.blackKingPos = (row, col)
                    col += 1

        for col in range(8):
            whitePawn = board.squares[6][col].piece
            if whitePawn and whitePawn.name == 'pawn' and whitePawn.colour == 'white':
                whitePawn.moved = False
            blackPawn = board.squares[1][col].piece
            if blackPawn and blackPawn.name == 'pawn' and blackPawn.colour == 'black':
                blackPawn.moved = False

        board.currentTurn = 'white' if turn == 'w' else 'black'

        board.castleRights[0] = 'K' in castling
        board.castleRights[1] = 'Q' in castling
        board.castleRights[2] = 'k' in castling
        board.castleRights[3] = 'q' in castling

        if board.castleRights[0] or board.castleRights[1]:
            king = board.squares[7][4].piece
            if king and king.name == 'king':
                king.moved = False
        if board.castleRights[2] or board.castleRights[3]:
            king = board.squares[0][4].piece
            if king and king.name == 'king':
                king.moved = False
        if board.castleRights[0]:
            rook = board.squares[7][7].piece
            if rook and rook.name == 'rook': rook.moved = False
        if board.castleRights[1]:
            rook = board.squares[7][0].piece
            if rook and rook.name == 'rook': rook.moved = False
        if board.castleRights[2]:
            rook = board.squares[0][7].piece
            if rook and rook.name == 'rook': rook.moved = False
        if board.castleRights[3]:
            rook = board.squares[0][0].piece
            if rook and rook.name == 'rook': rook.moved = False

        if enPassant != '-':
            enPassantCol = ord(enPassant[0]) - ord('a')
            enPassantRow = 8 - int(enPassant[1])
            board.enPassantTarget = (enPassantRow, enPassantCol)
        else:
            board.enPassantTarget = None

        board.halfmoveClock = int(halfmove)

        board.zobristHash = board.computePositionHash()
        board.positionHistory.append(board.zobristHash)

        return board