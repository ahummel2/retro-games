#!/usr/bin/python3

import os
import sys
import math
import time
import queue
import random
import pygame
import argparse
import traceback
import threading
from pygame.locals import *

class BlockGame:
	def __init__(self, screen, width, height, colors, x_scalar, y_scalar):
		self.rbg = [(255,0,0),(0,255,0),(0,0,255),(204,204,0),(204,0,204),(0,204,204),(255,255,255),(140,140,140)]
		self.width = int(width)
		self.height = int(height)
		self.x_scalar = int(x_scalar)
		self.y_scalar = int(y_scalar)
		self.colors = int(colors)
		self.screen = screen
		self.running = True
		self.score = 0
		self.moves = 0
		self.counter = 0
		self.map = [[None for y in range(self.height)] for x in range(self.width)]

		self.mid = int(math.floor(self.width / 2))
		self.shapes = {}
		self.current = self.place_new_shape(self.counter, self.mid, 0)
		self.shapes[self.counter] = self.current

	def place_new_shape(self, id, x, y):
		new_shape = BlockGame.Shape(id, x, y, color=random.randrange(self.colors), type=random.randrange(6), rotation=0)
		invalid_pos = False
		while(not invalid_pos):
			for block in new_shape.blocks:
				if block.y < 0:
					new_shape.update_pos(0, 1)
				else:
					invalid_pos = True
	
		for block in new_shape.blocks:
			if self.map[block.x][block.y] != None:
				self.game_over()
				print(block.x,block.y)
				print('game over caused')
				return
			self.map[block.x][block.y] = new_shape

		self.shapes[id] = new_shape
		return new_shape

	def draw_shape(self, shape):
		for block in shape.blocks:
			self.map[block.x][block.y] = shape

	def draw_board(self, screen):
		for x in range(self.width):
			for y in range(self.height):
				shape = self.map[x][y]
				if shape != None:
					#print('print blocks')
					for block in shape.blocks:
						#print(block.x,block.y)
						pygame.draw.rect(screen, self.rbg[block.color],
						    (self.x_scalar * block.x, self.y_scalar * block.y, self.x_scalar ,self.y_scalar))
				else:
					pygame.draw.rect(screen, (0,0,0),
					    (self.x_scalar * x, self.y_scalar * y, self.x_scalar ,self.y_scalar))

	def process_event(self, event):
		if event == 'EXIT' or event == K_ESCAPE:
			self.running = False
		if event in (K_LEFT, K_a):
			self.update_shape_position('left')
		if event in (K_RIGHT, K_d):
			self.update_shape_position('right')
		if event in (K_DOWN, K_s):
			self.update_shape_position('down')
		if event in (K_q,):
			self.rotate_shape('left')
		if event in (K_e,):
			self.rotate_shape('right')
		if event == MOUSEBUTTONDOWN:
			#game_instance.print_details()
			self.tick()
		return True
	
	def tick(self):
		self.update_shape_position('down')

	def print_details(self):
		for id in self.shapes:
			print(self.shapes[id].id,self.shapes[id].x,self.shapes[id].y)
	
	def rotate_shape(self, direction):
		##	could probably optimize this but it's simple enough for the time being
		shape = self.current
		if direction == 'right':
			if shape.rotation == 3:
				shape.rotation = 0
			else:
				shape.rotation += 1
		if direction == 'left':
			if shape.rotation == 0:
				shape.rotation = 3
			else:
				shape.rotation -= 1
		
		can_move = True
		for block in shape.blocks:
			##	Need to implement whatever logic is needed here to handle rotations in tight spaces
			##	may need to do this before the assignment above, and assign can_move=false
			pass
		if can_move == True:
			for block in shape.blocks:
				self.map[block.x][block.y] = None
			shape.update_rotation()
			self.draw_shape(shape)
		##	Need to think about how to handle rotating shapes in a close space
		##	Do I give up if the exact expected rotation doesnt fit
		##	Or look around for nearby positions that may fit

	def update_shape_position(self, dir, id=None):
		if dir == 'down':
			x_dir = 0
			y_dir = 1
		if dir == 'left':
			x_dir = -1
			y_dir = 0
		if dir == 'right':
			x_dir = 1
			y_dir = 0

		if id == None:
			shape = self.current
		else:
			shape = self.shapes[int(id)]

		if len(shape.blocks) == 0:
			return False

		can_move = True
		for block in shape.blocks:
			if block.y + y_dir >= self.height:
				can_move = False
				break
			if block.x + x_dir < 0 or block.x + x_dir > self.width - 1:
				can_move = False
				break
			#if block.y < self.height - 1:
			if self.map[block.x+x_dir][block.y+y_dir] != None:
				if self.map[block.x+x_dir][block.y+y_dir].id != shape.id:
					can_move = False
		if can_move == True:
			for block in shape.blocks:
				self.map[block.x][block.y] = None
			shape.update_pos(x_dir, y_dir)
			self.draw_shape(shape)
			return True
		else:
			##	Only do this on the down dir and only on the current block
			if dir == 'down' and id == None:
				##	Was not able to move down anymore.  this should trigger a new shape
				self.counter += 1
				self.current = self.place_new_shape(self.counter, self.mid, 0)
				self.shapes[self.counter] = self.current
				self.clear_full_lines()
			return False

	def clear_full_lines(self):
		lines_cleared = 0
		deletables = []
		for y in range(self.height):
			complete = True
			for x in range(self.width):
				if self.map[x][y] == None:
					complete = False
					break

			if complete:
				for x in range(self.width):
					##  Remove all of these blocks, ideally animated in some way so its not instant
					shape = self.map[x][y]
					for block in shape.blocks:
						if block.x == x and block.y == y:
							deletables.append(block)
							#shape.blocks.remove(block)
					#self.map[x][y] = None
				lines_cleared += 1

		if lines_cleared > 0:
			##	toggle the colors a bit then delete the blocks
			for i in range(4):
				for block in deletables:
					if block.color == 6:
						block.color = 7
					else:
						block.color = 6
				time.sleep(0.3)
				
			for block in deletables:
				shape = self.map[block.x][block.y]
				self.map[block.x][block.y] = None
				shape.blocks.remove(block)

			self.clean_up_dead_shapes()
			##  Move all remaining shapes/blocks down by 1
			for i in range(lines_cleared):
				for id in self.shapes:
					self.update_shape_position('down', id)

		return lines_cleared

	def clean_up_dead_shapes(self):
		deletables = []
		for id in self.shapes:
			if len(self.shapes[id].blocks) == 0:
				deletables.append(id)

		for id in deletables:
			self.shapes.pop(id)

	def score_calc(self, rows_cleared):
		return rows_cleared

	def game_over(self):
		self.running = False
	
	def get_state(self):
		return self.running

	class Block:
		def __init__(self, shape_id, id, x, y, color):
			self.shape_id = int(shape_id)
			self.id = int(id)
			self.x = int(x)
			self.y = int(y)
			self.color = int(color)

	class Shape:
		def __init__(self, id, x, y, color=color, type=0, rotation=0):
			self.id = int(id)
			self.x = int(x)
			self.y = int(y)
			self.color = int(color)
			self.type = int(type)
			self.blocks = []
			self.rotation = rotation
			
			##	Need to define block shapes to avoid confusion
			##	0, long piece
			##	1, l piece right
			##	2, l piece left
			##	3, square
			##	4, zag right
			##	5, zag left
			##	6, 3 sider
			long_rotations =	[[(-1,0),(0,0),(1,0),(2,0)],	[(1,-1),(1,0),(1,1),(1,2)],	[(2,-1),(1,-1),(0,-1),(-1,-1)],	[(0,-2),(0,-1),(0,0),(0,1)]]
			l_left_rotations =	[[(-1,-1),(-1,0),(0,0),(1,0)],	[(1,-1),(0,-1),(0,0),(0,1)],[(1,1),(1,0),(0,0),(-1,0)],		[(-1,1),(0,1),(0,0),(0,-1)]]
			l_right_rotations =	[[(-1,0),(0,0),(1,0),(1,-1)],	[(0,-1),(0,0),(0,1),(1,1)],	[(1,0),(0,0),(-1,0),(-1,1)],	[(0,1),(0,0),(0,-1),(-1,-1)]]
			square_rotations =	[[(-1,-1),(0,-1),(-1,0),(0,0)],	[(1,-1),(1,0),(0,-1),(0,0)],[(1,1),(0,1),(1,0),(0,0)],		[(-1,1),(-1,0),(0,1),(0,0)]]
			z_left_rotations =	[[(-1,-1),(0,-1),(0,0),(1,0)],	[(1,-1),(1,0),(0,0),(0,1)],	[(1,1),(0,1),(0,0),(-1,0)],		[(-1,1),(-1,0),(0,0),(0,-1)]]
			z_right_rotations =	[[(-1,0),(0,0),(0,-1),(1,-1)],	[(0,-1),(0,0),(1,0),(1,1)],	[(1,0),(0,0),(0,1),(-1,1)],		[(0,1),(0,0),(-1,0),(-1,-1)]]
			pyramid_rotations =	[[(-1,0),(0,-1),(1,0),(0,0)],	[(0,-1),(1,0),(0,1),(0,0)],	[(1,0),(0,1),(-1,0),(0,0)],		[(0,1),(-1,0),(0,-1),(0,0)]]
			
			self.rotations = [long_rotations, l_left_rotations, l_right_rotations, square_rotations, z_left_rotations, z_right_rotations, pyramid_rotations]
			
			self.blocks.append(BlockGame.Block(self.id,0,self.x + self.rotations[self.type][rotation][0][0],self.y + self.rotations[self.type][rotation][0][1],self.color))
			self.blocks.append(BlockGame.Block(self.id,1,self.x + self.rotations[self.type][rotation][1][0],self.y + self.rotations[self.type][rotation][1][1],self.color))
			self.blocks.append(BlockGame.Block(self.id,2,self.x + self.rotations[self.type][rotation][2][0],self.y + self.rotations[self.type][rotation][2][1],self.color))
			self.blocks.append(BlockGame.Block(self.id,3,self.x + self.rotations[self.type][rotation][3][0],self.y + self.rotations[self.type][rotation][3][1],self.color))

		def update_pos(self, x_diff, y_diff):
			self.x += x_diff
			self.y += y_diff
			for block in self.blocks:
				block.x += x_diff
				block.y += y_diff
		
		def update_rotation(self):
			rotation_values = self.rotations[self.type][self.rotation]
			for block in self.blocks:
				block.x = self.x + rotation_values[block.id][0]
				block.y = self.y + rotation_values[block.id][1]

def screen_draw_thread(running):
	while True:
		game_instance.draw_board(screen)
		pygame.display.flip()
		if not running():
			break

def main():
	##	In windows this doesn't work unless there's an x-server running
	##	Need to start up mobaXterm and the x-server through that to get the window to appear
	os.environ['SDL_AUDIODRIVER'] = 'dummy'
	os.environ['SDL_VIDEODRIVER'] = 'x11'
	os.environ['DISPLAY'] = 'localhost:0.0'
	pygame.init()
	random.seed()
	
	parser = argparse.ArgumentParser(description='Tetris clone')
	parser.add_argument('-g', '--grid', type=str, default='14x16', help='size of the gameboard, WxH')
	parser.add_argument('-c', '--colors', type=int, default=5, help='number of colors to use')
	#parser.add_argument('-m', '--moves', type=int, default=20, help='number of moves allowed in a game')
	parser.add_argument('-s', '--size', type=str, default='640x480', help='size of the game screen')

	args = parser.parse_args()

	grid_width, grid_height = [int(numeric_string) for numeric_string in args.grid.split('x')]
	screen_width, screen_height = [int(numeric_string) for numeric_string in args.size.split('x')]

	x_scalar = math.floor(screen_width / grid_width)
	y_scalar = math.floor(screen_height / grid_height)

	##	ideally would like to do without global vars, I don't think it'd be easy to send updates
	##	quickly to the drawing thread though
	global screen, game_instance
	screen = pygame.display.set_mode((screen_width, screen_height))
	#pygame.time.Clock.tick(60)
	pygame.time.set_timer(pygame.USEREVENT, 1000)
	game_instance = BlockGame(screen, grid_width, grid_height, args.colors, x_scalar, y_scalar)

	running = True
	
	display_thread = threading.Thread(target = screen_draw_thread, args =(lambda : running, ))
	#display_thread = screen_draw_thread()
	display_thread.start()
	try:
		while(running):
			for event in pygame.event.get():
				if event.type == USEREVENT:
					##	move the piece down or create a new one
					game_instance.tick()
				if event.type == KEYDOWN:
					game_instance.process_event(event.key)
			running = game_instance.get_state()
	except:
		traceback.print_exc(file=sys.stdout)
		running = False
	finally:
		display_thread.join()		
	
if __name__ == "__main__":
	main()
