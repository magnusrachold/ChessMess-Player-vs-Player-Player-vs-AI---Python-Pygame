
from const import *
from board import Board
from dragger import Dragger
from config import Config
from square import Square

class Game:
    def __init__(self):
        self.board = Board()
        self.dragger = Dragger()
        self.nextTurn = 'white'
        self.currentHover = None
        self.config = Config()

    def updateNextTurn(self):
        self.nextTurn = 'black' if self.nextTurn == 'white' else 'white'

    def hoverSquare(self, row, col):
        if Square.isOnBoard(row, col):
            self.currentHover = self.board.squares[row][col]

    def playSoundEffect(self, hasCaptured = False):
        if hasCaptured:
            self.config.captureSound.play()
        else:
            self.config.moveSound.play()

    def restart(self):
        self.__init__()

    def isGameOver(self, colour):
        allMoves = []
        remainingPieces = []
        for r in range(ROWS):
            for c in range(COLS):
                square = self.board.squares[r][c]
                if square.hasPiece():
                    if square.piece.colour == colour:
                        tempMoves = []
                        self.board.calculateMoves(square.piece, r, c, tempMoves, isTemporary = True, filterSafe = True)
                        allMoves.extend(tempMoves)
                    remainingPieces.append(square.piece)

        if self.isInsufficientMaterial(remainingPieces):
            return "insufficientMaterial"
        if self.checkThreefoldRepetition():
            return "threefoldRepetition"
        if self.checkFiftyMoveRule():
            return "fiftyMoveRule"

        if len(allMoves) == 0:
            if self.board.isInCheck(colour):
                return "checkmate"
            else:
                return "stalemate"
        return None

    def checkFiftyMoveRule(self):
        return self.board.halfmoveClock >= 100

    def checkThreefoldRepetition(self):
        if not self.board.positionHistory:
            return False

        currentPos = self.board.positionHistory[-1]
        count = self.board.positionHistory.count(currentPos)

        return count >= 3

    def isInsufficientMaterial(self, pieces):
        if len(pieces) > 4:
            return False
        if len(pieces) == 2:
            return True
        if len(pieces) == 3:
            return any(p.name in ['bishop', 'knight'] for p in pieces)
        if len(pieces) == 4:
            bishops = [p for p in pieces if p.name == 'bishop']
            if len(bishops) == 2 and bishops[0].colour != bishops[1].colour:
                return True
            knights = [p for p in pieces if p.name == 'knight']
            if len(knights) == 2:
                return True
            if len(bishops) == 1 and len(knights) == 1 and (bishops[0].colour != knights[0].colour):
                return True
        return False

    # initialize and display background
    def showBackground(self, screen):
        font = pygame.font.SysFont('Arial', 14, bold=True)
        for row in range(ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 0:
                    colour = (225, 200, 180) # light brown
                    textColour = (95, 60, 25)
                else:
                    colour = (95, 60, 25) # dark brown
                    textColour = (225, 200, 180)
                rect = (col * SquareSize, row * SquareSize, SquareSize, SquareSize)
                pygame.draw.rect(screen, colour, rect)

                # add number labels to the leftmost column
                if col == 0:
                    labelY = font.render(str(8 - row), True, textColour)
                    screen.blit(labelY, (col * SquareSize + 5, row * SquareSize + 2))

                # add letter labels to the bottom row
                if row == 7:
                    labelX = font.render(chr(97 + col), True, textColour)
                    textWidth = labelX.get_width()
                    screen.blit(labelX, (col * SquareSize + SquareSize - textWidth - 5, row * SquareSize + SquareSize - 20))


    def showPieces(self, screen):
        for row in range(ROWS):
            for col in range(COLS):
                if self.board.squares[row][col].hasPiece():
                    piece = self.board.squares[row][col].piece

                    if piece is not self.dragger.piece:
                        img = piece.image
                        padding = 10  # 10 pixels of distance to the edges of the rectangle
                        innerSize = SquareSize - padding
                        scaledImage = pygame.transform.smoothscale(img, (innerSize, innerSize))
                        offset = padding // 2
                        screen.blit(scaledImage, (col * SquareSize + offset, row * SquareSize + offset))


    def showMoves(self, screen):
        if self.dragger.isActive:
            piece = self.dragger.piece
            # highlight possible moves
            for move in piece.moves:
                colour = '#C86464' if (move.destinationSquare.row + move.destinationSquare.col) % 2 == 0 else '#C84646'
                rect = (move.destinationSquare.col * SquareSize, move.destinationSquare.row * SquareSize, SquareSize, SquareSize)
                pygame.draw.rect(screen, colour, rect)

    def showLastMove(self, screen):
        if self.board.lastMove:
            initialSquare = self.board.lastMove.initialSquare
            destinationSquare = self.board.lastMove.destinationSquare
            for square in [initialSquare, destinationSquare]:
                colour = '#C8A864' if (square.row + square.col) % 2 == 0 else '#C89646'
                rect = (square.col * SquareSize, square.row * SquareSize, SquareSize, SquareSize)
                pygame.draw.rect(screen, colour, rect)

    def showHover(self, screen):
        if self.currentHover:
            colour = (186, 202, 68)
            rect = (self.currentHover.col * SquareSize, self.currentHover.row * SquareSize, SquareSize, SquareSize)
            pygame.draw.rect(screen, colour, rect, width = 3)

    def updateScreen(self, screen):
        self.showBackground(screen)
        self.showLastMove(screen)
        self.showMoves(screen)
        self.showPieces(screen)

