import sys

from const import *
from gameState import Game
from move import Move

class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('ChessMess')
        self.game = Game()
        self.promotionActive = False
        self.promotionPos = None
        self.promotionColour = None
        self.promotionRect = None

    def mainloop(self):
        board = self.game.board
        dragger = self.game.dragger

        while True:
            self.game.updateScreen(self.screen)
            self.game.showHover(self.screen)

            if self.promotionActive:
                self.drawPromotionMenu()

            if dragger.isActive:
                dragger.updateImage(self.screen)

            for event in pygame.event.get():

                if event.type == pygame.MOUSEBUTTONDOWN: # click
                    if self.promotionActive:
                        self.handlePromotion(event.pos, board)
                        continue
                    dragger.updateMousePos(event.pos)
                    clickedCol = dragger.mouseXCoord // SquareSize
                    clickedRow = dragger.mouseYCoord // SquareSize

                    if board.squares[clickedRow][clickedCol].hasPiece():
                        piece = board.squares[clickedRow][clickedCol].piece
                        if piece.colour == self.game.nextTurn:
                            board.calculateMoves(piece, clickedRow, clickedCol)
                            dragger.savePos(event.pos)
                            dragger.savePiece(piece)
                            self.game.updateScreen(self.screen)

                elif event.type == pygame.MOUSEMOTION: # drag
                    motionRow = event.pos[1] // SquareSize
                    motionCol = event.pos[0] // SquareSize
                    self.game.hoverSquare(motionRow, motionCol)

                    if dragger.isActive:
                        dragger.updateMousePos(event.pos)
                        self.game.updateScreen(self.screen)
                        self.game.showHover(self.screen)
                        dragger.updateImage(self.screen)

                elif event.type == pygame.MOUSEBUTTONUP: # release
                    if dragger.isActive:
                        dragger.updateMousePos(event.pos)
                        releasedCol = dragger.mouseXCoord // SquareSize
                        releasedRow = dragger.mouseYCoord // SquareSize
                        move = Move.createNewMove(dragger.initialRow, dragger.initialCol, releasedRow, releasedCol)
                        matchingMove = next((m for m in dragger.piece.moves if m == move), None)
                        if matchingMove and board.isValidMove(dragger.piece, move):
                            hasCaptured = board.squares[releasedRow][releasedCol].hasPiece()
                            board.movePiece(dragger.piece, matchingMove)
                            self.game.playSoundEffect(hasCaptured)
                            if board.promotionPending:
                                self.promotionActive = True
                                self.promotionPos = (releasedRow, releasedCol)
                                self.promotionColour = dragger.piece.colour
                            else:
                                self.game.updateNextTurn()
                                self.game.updateScreen(self.screen)
                                status = self.game.isGameOver(self.game.nextTurn)
                                if status == "checkmate":
                                    print(f"CHECKMATE! {self.game.nextTurn} has lost!")
                                elif status == "stalemate":
                                    print(f"DRAW because {self.game.nextTurn} has no valid move!")
                                elif status == "insufficientMaterial":
                                    print("DRAW due to insufficient material!")
                                elif status == "threefoldRepetition":
                                    print("DRAW due to threefold repetition!")
                                elif status == "fiftyMoveRule":
                                    print("DRAW due to 50 moves without progress!")

                    dragger.clearPiece()

                elif event.type == pygame.KEYDOWN:  # key pressed
                    if event.key == pygame.K_r:
                        self.game.restart()
                        board = self.game.board
                        dragger = self.game.dragger

                elif event.type == pygame.QUIT:     # exit
                    pygame.quit()
                    sys.exit()

            pygame.display.update()

    def handlePromotion(self, pos, board):
        if self.promotionRect and self.promotionRect.collidepoint(pos):
            xCoord, yCoord = pos
            choiceIndex = (xCoord - self.promotionRect.x) // SquareSize
            pieceTypes = ['queen', 'rook', 'bishop', 'knight']
            selectedType = pieceTypes[choiceIndex]

            board.completePromotion(self.promotionPos[0],self.promotionPos[1], self.promotionColour, selectedType)
            self.game.playSoundEffect(hasCaptured = False)
            self.promotionActive = False
            self.promotionRect = None

            self.game.updateNextTurn()
            self.game.updateScreen(self.screen)
            status = self.game.isGameOver(self.game.nextTurn)
            if status == "checkmate":
                print("CHECKMATE!")
            elif status == "stalemate":
                print("DRAW!")

    def drawPromotionMenu(self):
        if not self.promotionActive:
            return
        row, col = self.promotionPos  # Position des Bauern
        colour = self.promotionColour  # 'w' oder 'b'
        choices = [colour + '-queen', colour + '-rook', colour + '-bishop', colour + '-knight']

        xStart = col * SquareSize
        if col > 4:
            xStart = (col - 3) * SquareSize
        yStart = row * SquareSize
        if row == 0: yStart += SquareSize
        else: yStart -= SquareSize

        menuRect = pygame.Rect(xStart, yStart, 4 * SquareSize, SquareSize)
        self.promotionRect = menuRect
        pygame.draw.rect(self.screen, (240, 217, 181), menuRect, border_radius = 15)
        pygame.draw.rect(self.screen, (139, 69, 19), menuRect, 3, border_radius = 15)

        mousePos = pygame.mouse.get_pos()
        if menuRect.collidepoint(mousePos):
            hoverIndex = (mousePos[0] - menuRect.x) // SquareSize

            highlightSurface = pygame.Surface((SquareSize, SquareSize), pygame.SRCALPHA)
            pygame.draw.rect(highlightSurface, (255, 255, 255, 60), (0, 0, SquareSize, SquareSize), border_radius=15)
            highlightPos = (menuRect.x + hoverIndex * SquareSize, menuRect.y)
            self.screen.blit(highlightSurface, highlightPos)

        for i, pieceCode in enumerate(choices):
            img = IMAGES[pieceCode]
            padding = 5
            innerSize = SquareSize - padding
            scaledImage = pygame.transform.smoothscale(img, (innerSize, innerSize))
            offset = padding // 2
            self.screen.blit(scaledImage, (xStart + i * SquareSize + offset, yStart + offset))

main = Main()
main.mainloop()

