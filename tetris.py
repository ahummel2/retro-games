#!/usr/bin/python2.7

import os
import sys
import math
import time
import random
import pygame
import numpy
from pygame.locals import *
import argparse

class BlockGame:
	def __init__(self, screen, width, height, colors, x_scalar, y_scalar):
		self.rbg = [(255,0,0),(0,255,0),(0,0,255),(204,204,0),(204,0,204),(0,204,204), (255,255,255)]
		self.width = int(width)
		self.height = int(height)
		self.x_scalar = int(x_scalar)
		self.y_scalar = int(y_scalar)
		self.colors = int(colors)
		self.screen = screen
		self.score = 0
		self.moves = 0
		self.counter = 0
		self.map = [[None for y in range(self.height)] for x in range(self.width)]

		self.mid = int(math.floor(self.width / 2))
		self.shapes = {}
		self.current = self.place_new_shape(self.counter, self.mid, 0)
		self.shapes[self.counter] = self.current

	def place_new_shape(self, id, x, y):
		new_shape = BlockGame.Shape(id, x, y, random.randrange(self.colors), random.randrange(3))
		for block in new_shape.blocks:
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

	def tick(self):
		success = self.update_shape_position(None, 'down')
		##  Unable to move down, if this was triggered by the tick, create a new block
		if not success:
			self.counter += 1
			self.current = self.place_new_shape(self.counter, self.mid, 0)
			self.shapes[self.counter] = self.current
			self.clear_full_lines()
		return

	def print_details(self):
		for id in self.shapes:
			print(self.shapes[id].id,self.shapes[id].x,self.shapes[id].y)

	def handle_button_press(self, coords):
		x, y = coords
		x_coord = int(math.floor(x / self.x_scalar))
		y_coord = int(math.floor(y / self.y_scalar))
		source = self.map[x_coord][y_coord]
		self.map[x_coord][y_coord] = None
		self.delete_similar_block(source.x, source.y, source.color)
		self.update_block_positions()
		num_created = self.create_new_blocks()
		self.score += self.score_calc(num_created)
		self.moves += 1

	def update_shape_position(self, id, dir):
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
			for block in deletables:
				block.color = 6
				##  Not working, but maybe if I split the drawing and game portion into different threads
				##  this may update and draw.  think the tick isn't being triggered because this is stalling
				##  until the rest of the function continues erasing the work
			self.draw_board(self.screen)
			time.sleep(1)
			for block in deletables:
				shape = self.map[block.x][block.y]
				self.map[block.x][block.y] = None
				shape.blocks.remove(block)

			self.clean_up_dead_shapes()
			##  Move all remaining shapes/blocks down by 1
			for i in range(lines_cleared):
				for id in self.shapes:
					self.update_shape_position(id, 'down')

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
		return False

	class Block:
		def __init__(self, shape_id, id, x, y, color):
			self.shape_id = int(shape_id)
			self.id = int(id)
			self.x = int(x)
			self.y = int(y)
			self.color = int(color)

	class Shape:
		def __init__(self, id, x, y, color, type):
			self.id = int(id)
			self.x = int(x)
			self.y = int(y)
			self.color = int(color)
			self.type = int(type)
			self.blocks = []

			##  Need to create the shape types here
			if self.type == 0:
				self.blocks.append(BlockGame.Block(self.id,0,self.x,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,1,self.x+1,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,2,self.x,self.y+1,self.color))
				self.blocks.append(BlockGame.Block(self.id,3,self.x+1,self.y+1,self.color))
			if self.type == 1:
				self.blocks.append(BlockGame.Block(self.id,0,self.x,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,1,self.x+1,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,2,self.x+2,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,3,self.x+3,self.y,self.color))
			if self.type == 2:
				self.blocks.append(BlockGame.Block(self.id,0,self.x,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,1,self.x+1,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,2,self.x+1,self.y+1,self.color))
				self.blocks.append(BlockGame.Block(self.id,3,self.x+2,self.y+1,self.color))
			if self.type == 3:
				self.blocks.append(BlockGame.Block(self.id,0,self.x,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,1,self.x,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,2,self.x,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,3,self.x,self.y,self.color))
			if self.type == 4:
				self.blocks.append(BlockGame.Block(self.id,0,self.x,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,1,self.x,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,2,self.x,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,3,self.x,self.y,self.color))
			if self.type == 5:
				self.blocks.append(BlockGame.Block(self.id,0,self.x,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,1,self.x,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,2,self.x,self.y,self.color))
				self.blocks.append(BlockGame.Block(self.id,3,self.x,self.y,self.color))

		def update_pos(self, x_diff, y_diff):
			self.x += x_diff
			self.y += y_diff
			for block in self.blocks:
				block.x += x_diff
				block.y += y_diff


def main():
	pygame.init()
	random.seed()
	
	parser = argparse.ArgumentParser(description='Basic block busting game demo')
	parser.add_argument('-g', '--grid', type=str, default='8x8', help='size of the gameboard, WxH')
	parser.add_argument('-c', '--colors', type=int, default=3, help='number of colors to use')
	#parser.add_argument('-m', '--moves', type=int, default=20, help='number of moves allowed in a game')
	parser.add_argument('-s', '--size', type=str, default='320x240', help='size of the game screen')

	args = parser.parse_args()

	grid_width, grid_height = [int(numeric_string) for numeric_string in args.grid.split('x')]
	screen_width, screen_height = [int(numeric_string) for numeric_string in args.size.split('x')]

	x_scalar = math.floor(screen_width / grid_width)
	y_scalar = math.floor(screen_height / grid_height)

	screen = pygame.display.set_mode((screen_width, screen_height))
	instance = BlockGame(screen, grid_width, grid_height, args.colors, x_scalar, y_scalar)

	running = True
	while(running):
		if instance.game_over():
			print('Final Score:', int(instance.score))
			running=False
			break
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == KEYDOWN and event.key == K_ESCAPE:
				running = False
			elif event.type == KEYDOWN and event.key == K_LEFT:
				instance.update_shape_position(None, 'left')
			elif event.type == KEYDOWN and event.key == K_RIGHT:
				instance.update_shape_position(None, 'right')
			elif event.type == KEYDOWN and event.key == K_DOWN:
				instance.update_shape_position(None, 'down')
			elif event.type == MOUSEBUTTONDOWN:
				instance.print_details()
				instance.tick()

		instance.draw_board(screen)
		pygame.display.flip()
			
	
if __name__ == "__main__":
	main()
