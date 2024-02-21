import sys
import os
import random
from datetime import datetime
import pygame
import math

class Vector2:
	def __init__( self, x, y ):
		self.x = x
		self.y= y
	def add( self, other ):
		self.x += other.x
		self.y += other.y
	def sub( self, other ):
		self.x -= other.x
		self.y -= other.y
	def mul( self, other ):
		self.x *= other.x
		self.y *= other.y
	def div( self, other ):
		self.x /= other.x
		self.y /= other.y

class Rect:
	def __init__( self, x, y, w, h ):
		self.x = x
		self.y = y
		self.w = w
		self.h = h
	def isPointIn( self, point : Vector2 ):
		return self.x <= point.x and self.y <= point.x and point.x <= self.x + self.w and point.y <= self.y + self.h

class InputManager:
	def __init__( self ):
		self.mouseButtonPressed = [ False, False, False, False, False ]
		self.mouseButtonHeld = [ False, False, False, False, False ]
		self.mousePos = Vector2( 0, 0 )
		self.keys = []
	def pollInputs( self ):
		for i in range( len( self.mouseButtonPressed ) ):
			self.mouseButtonPressed[i] = False

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return False
			if event.type == pygame.MOUSEBUTTONDOWN:
				self.mouseButtonPressed = list( pygame.mouse.get_pressed() )
				self.mouseButtonHeld = list( pygame.mouse.get_pressed() )
			if event.type == pygame.MOUSEBUTTONUP:
				self.mouseButtonHeld = list( pygame.mouse.get_pressed() )
			if event.type == pygame.MOUSEMOTION:
				self.mousePos.x = event.pos[0] / ( game.screen.get_width() / game.resolution.x )
				self.mousePos.y = event.pos[1] / ( game.screen.get_height() / game.resolution.y )
			if event.type == pygame.KEYDOWN or pygame.KEYUP:
				self.keys = pygame.key.get_pressed()

				if self.keys[ pygame.K_ESCAPE ]:
					return False
		return True

class Tile:
	def __init__( self ):
		self.isBlock = True
		self.hasMine = False
		self.exploded = False
		self.hasFlag = False
		self.minesNextTo = 0
		self.clearing = False

	def draw( self, pos : Vector2 ):
		if self.isBlock:
			game.framebuffer.blit(
				game.textures[ "tiles" ],
				( pos.x, pos.y ),
				[ game.TILE_SIZE, 0, game.TILE_SIZE, game.TILE_SIZE ]
			)
		else:
			game.framebuffer.blit(
				game.textures[ "tiles" ],
				( pos.x, pos.y ),
				[ 0, 0, game.TILE_SIZE, game.TILE_SIZE ]
			)
			if 0 < self.minesNextTo:
				game.framebuffer.blit(
					game.textures[ "numbersCol" ],
					( pos.x, pos.y ),
					[ self.minesNextTo * game.TILE_SIZE, 0, game.TILE_SIZE, game.TILE_SIZE ]
				)

		if game.state == game.STATE_FAIL and self.hasMine:
			game.framebuffer.blit(
				game.textures[ "tiles" ],
				( pos.x, pos.y ),
				[ 7 * game.TILE_SIZE, 0, game.TILE_SIZE, game.TILE_SIZE ]
			)
		if self.hasFlag:
			game.framebuffer.blit(
				game.textures[ "tiles" ],
				( pos.x, pos.y ),
				[ 6 * game.TILE_SIZE, 0, game.TILE_SIZE, game.TILE_SIZE ]
			)
		if self.exploded:
			game.framebuffer.blit(
				game.textures[ "tiles" ],
				( pos.x, pos.y ),
				[ 8 * game.TILE_SIZE, 0, game.TILE_SIZE, game.TILE_SIZE ]
			)

class Field:
	def __init__( self ):
		self.size = game.fieldSize
		self.tiles = []
		self.mineCount = 0

	def start( self, mineCount, size ):
		self.size = size
		self.mineCount = mineCount
		self.tiles.clear()

		for x in range( self.size.x ):
			self.tiles.append( [] )
			for y in range( self.size.y ):
				self.tiles[x].append( Tile() )
		self.spreadMines()

	def spreadMines( self ):
		total = self.mineCount

		while 0 < total:
			pos = Vector2( random.randint( 0, self.size.x - 1 ), random.randint( 0, self.size.y - 1 ) )
			if not self.tiles[ pos.x ][ pos.y ].hasMine:
				self.tiles[ pos.x ][ pos.y ].hasMine = True
				self.tiles[ pos.x ][ pos.y ].textureSrcX = 7 * game.TILE_SIZE
				total -= 1
		self.countNeighbourMines()

	def isInsideField( self, tilePos : Vector2 ):
		return 0 <= tilePos.x and tilePos.x < self.size.x and 0 <= tilePos.y and tilePos.y < self.size.y

	def countNeighbourMines( self ):
		for x in range( self.size.x ):
			for y in range( self.size.y ):
				if self.tiles[x][y].hasMine:
					continue
				for nx in range( -1, 2 ):
					for ny in range( -1, 2 ):
						pos = Vector2( x + nx, y + ny )
						if self.isInsideField( pos ) and self.tiles[ pos.x ][ pos.y ].hasMine:
							self.tiles[x][y].minesNextTo += 1
	def getTilePos( self ):
		mousePos = inputManager.mousePos
		return Vector2( math.floor( mousePos.x / game.TILE_SIZE ), math.floor( mousePos.y / game.TILE_SIZE ) - 1 )

	def checkWin( self ):
		for x in range( self.size.x ):
			for y in range( self.size.y ):
				tile = self.tiles[x][y]

				if tile.hasMine and not tile.hasFlag:
					return False
				elif tile.hasFlag and not tile.hasMine:
					return False
		return True

	def checkExpand( self, pos : Vector2 ):
		if self.isInsideField( pos ):
			tile = self.tiles[ pos.x ][ pos.y ]
			return tile.isBlock
		return False

	def expandClear( self, pos : Vector2 ):
		safe = 0
		frontier = [ pos ]
		visited = set()

		while 0 < len( frontier ):
			curPos = frontier.pop()

			if self.tiles[ curPos.x ][ curPos.y ].minesNextTo == 0:
				for y in range( -1, 2 ):
					for x in range( -1, 2 ):
						checkPos = Vector2( curPos.x + x, curPos.y + y )

						if self.checkExpand( checkPos ) and self.tiles[ checkPos.x ][ checkPos.y ] not in visited:
							frontier.append( checkPos )
							visited.add( self.tiles[ checkPos.x ][ checkPos.y ] )

			self.tiles[ curPos.x ][ curPos.y ].isBlock = False

	def update( self ):
		if inputManager.mouseButtonPressed[0]:
			tilePos = self.getTilePos()

			if self.isInsideField( tilePos ):
				tile = self.tiles[ tilePos.x ][ tilePos.y ]

				if tile.hasMine:
					tile.exploded = True
					game.state = game.STATE_FAIL
				elif tile.isBlock:
					tile.hasFlag = False
					tile.isBlock = False
					if tile.minesNextTo == 0:
						self.expandClear( tilePos )

		if inputManager.mouseButtonPressed[2]:
			tilePos = self.getTilePos()

			if self.isInsideField( tilePos ):
				tile = self.tiles[ tilePos.x ][ tilePos.y ]
				
				if tile.isBlock:
					tile.hasFlag = not tile.hasFlag
					if self.checkWin():
						game.state = game.STATE_WIN

	def draw( self ):
		for x in range( self.size.x ):
			for y in range( self.size.y ):
				self.tiles[x][y].draw( Vector2( x * game.TILE_SIZE, ( 1 + y ) * game.TILE_SIZE ) )

class Gui:
	def __init__( self ):
		self.faceSrc = Rect( 0, 0, 0, 0 )
		self.faceDst = Rect( 0, 0, 0, 0 )
		self.mineDst = Rect( 0, 0, 0, 0 )
		self.sizeDst = Rect( 0, 0, 0, 0 )
		self.mineCount = 10
		self.fieldSize = 10
		self.adjust()

	def adjust( self ):
		self.faceSrc = Rect( game.TILE_SIZE * 2, 0, game.TILE_SIZE, game.TILE_SIZE )
		self.faceDst = Rect( game.resolution.x / 2 - game.TILE_SIZE / 2, 0, self.faceSrc.w, self.faceSrc.h )
		self.mineDst = Rect( 0, 0, game.TILE_SIZE, game.TILE_SIZE )
		self.sizeDst = Rect( game.resolution.x - game.TILE_SIZE * 3, 0, game.TILE_SIZE, game.TILE_SIZE )

	def update( self ):
		if inputManager.mouseButtonPressed[0]:
			if self.faceDst.isPointIn( inputManager.mousePos ):
				game.start( self.mineCount, self.fieldSize )
			elif self.mineDst.isPointIn( inputManager.mousePos ) and self.mineCount < 99:
				self.mineCount += 1
			elif self.sizeDst.isPointIn( inputManager.mousePos ) and self.fieldSize < 40:
				self.fieldSize += 1
		elif inputManager.mouseButtonPressed[2]:
			if self.mineDst.isPointIn( inputManager.mousePos ) and 1 < self.mineCount:
				self.mineCount -= 1
			elif self.sizeDst.isPointIn( inputManager.mousePos ) and 10 < self.fieldSize:
				self.fieldSize -= 1

	def drawNumber( self, pos, value ):
		game.framebuffer.blit(
			game.textures[ "numbers" ],
			[ pos.x, pos.y ],
			[ math.floor( value / 10 ) * game.TILE_SIZE, 0, game.TILE_SIZE, game.TILE_SIZE ]
		)
		game.framebuffer.blit(
			game.textures[ "numbers" ],
			[ pos.x + game.TILE_SIZE, pos.y ],
			[ value % 10 * game.TILE_SIZE, 0, game.TILE_SIZE, game.TILE_SIZE ]
		)
	def draw( self ):
		if game.state == game.STATE_RUN and inputManager.mouseButtonHeld[0]:
			self.faceSrc.x = game.TILE_SIZE * 3
		else:
			if game.state == game.STATE_RUN:
				self.faceSrc.x = game.TILE_SIZE * 2
			elif game.state == game.STATE_FAIL:
				self.faceSrc.x = game.TILE_SIZE * 4
			elif game.state == game.STATE_WIN:
				self.faceSrc.x = game.TILE_SIZE * 5
		# Face.
		game.framebuffer.blit(
			game.textures[ "tiles" ],
			[ self.faceDst.x, self.faceDst.y ],
			[ self.faceSrc.x, self.faceSrc.y, self.faceSrc.w, self.faceSrc.h ]
		)
		# Mine count
		game.framebuffer.blit(
			game.textures[ "tiles" ],
			[ self.mineDst.x, self.mineDst.y ],
			[ 7 * game.TILE_SIZE, 0, self.mineDst.w, self.mineDst.h ]
		)
		self.drawNumber( Vector2( 8, 0 ), self.mineCount )
		# Field size
		game.framebuffer.blit(
			game.textures[ "tiles" ],
			[ self.sizeDst.x, self.sizeDst.y ],
			[ 9 * game.TILE_SIZE, 0, self.sizeDst.w, self.sizeDst.h ]
		)
		self.drawNumber( Vector2( self.sizeDst.x + game.TILE_SIZE, 0 ), self.fieldSize )

class Game:
	TILE_SIZE = 8
	WIN_SCALE = 5
	STATE_RUN = 1
	STATE_FAIL = 2
	STATE_WIN = 3

	def __init__( self ):
		self.fieldSize = Vector2( 10, 10 )
		self.resolution = Vector2( self.fieldSize.x * self.TILE_SIZE, self.fieldSize.y * self.TILE_SIZE + self.TILE_SIZE )
		self.framebuffer = pygame.Surface( ( self.resolution.x, self.resolution.y ) )
		self.screen = pygame.display.set_mode( ( self.resolution.x * self.WIN_SCALE, self.resolution.y * self.WIN_SCALE ), pygame.RESIZABLE )
		self.clock = pygame.time.Clock()
		self.textures = {}
		self.running = True
		self.state = self.STATE_RUN
		self.delta = 0
		self.loadResources()
	def start( self, mineCount, fieldSize ):
		self.state = self.STATE_RUN

		if fieldSize != self.fieldSize.x:
			self.fieldSize = Vector2( fieldSize, fieldSize )
			self.resolution = Vector2( self.fieldSize.x * self.TILE_SIZE, self.fieldSize.y * self.TILE_SIZE + self.TILE_SIZE )
			self.framebuffer = pygame.Surface( ( self.resolution.x, self.resolution.y ) )
			self.screen = pygame.display.set_mode( ( self.resolution.x * self.WIN_SCALE, self.resolution.y * self.WIN_SCALE ), pygame.RESIZABLE )

		gui.adjust()
		field.start( mineCount, self.fieldSize )

	def loadResources( self ):
		self.textures[ "tiles" ] = pygame.image.load( os.getcwd() + "/Images/tiles.png" )
		self.textures[ "numbers" ] = pygame.image.load( os.getcwd() + "/Images/numbers.png" )
		self.textures[ "numbersCol" ] = pygame.image.load( os.getcwd() + "/Images/numbersCol.png" )

	def update( self ):
		while self.running:
			self.running = inputManager.pollInputs()
			self.delta = self.clock.tick( 60 ) / 1000

			if self.state == self.STATE_RUN:
				field.update()
			gui.update()
			self.draw()

	def draw( self ):
		clearColor = ( 75, 75, 75 )
		self.screen.fill( clearColor )
		self.framebuffer.fill( clearColor )
		field.draw()
		gui.draw()
		self.screen.blit( pygame.transform.scale( self.framebuffer, self.screen.get_rect().size ), ( 0, 0 ) )
		pygame.display.flip()

pygame.init()
pygame.display.set_caption( "Minesweeper" )
pygame.display.set_icon( pygame.image.load( os.getcwd() + "/Images/icon.png" ) )
random.seed( datetime.now().timestamp() )

inputManager = InputManager()
game = Game()
field = Field()
gui = Gui()

game.start( gui.mineCount, gui.fieldSize )
game.update()

pygame.quit()
