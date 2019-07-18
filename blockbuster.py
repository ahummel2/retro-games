#!/usr/bin/python2.7

import os
import sys
import math
import random
import pygame
from pygame.locals import *
import argparse

class BlockGame:
	def __init__(self, width, height, colors, x_scalar, y_scalar):
		self.rbg = [(255,0,0),(0,255,0),(0,0,255),(204,204,0),(204,0,204),(0,204,204)]
		self.width = int(width)
		self.height = int(height)
		self.x_scalar = int(x_scalar)
		self.y_scalar = int(y_scalar)
		self.colors = int(colors)
		self.score = 0
		self.moves = 0
		self.map = [[None for y in range(self.height)] for x in range(self.width)]
		for x in range(self.width):
			for y in range(self.height):
				self.map[x][y] = BlockGame.Block(x,y,random.randrange(self.colors))
	
	def draw_board(self, screen):
		for x in range(self.width):
			for y in range(self.height):
				block = self.map[x][y]
				if block != None:
					pygame.draw.rect(screen, self.rbg[block.color],
					    (self.x_scalar * x, self.y_scalar * y, self.x_scalar ,self.y_scalar))
				else:
					pygame.draw.rect(screen, (0,0,0),
					    (self.x_scalar * x, self.y_scalar * y, self.x_scalar ,self.y_scalar))

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

	def delete_similar_block(self, x, y, color):
		potentials = []
		if x > 0:
			potentials.append(self.map[x - 1][y])
		if x < self.width - 1:
			potentials.append(self.map[x + 1][y])
		if y > 0:
			potentials.append(self.map[x][y - 1])
		if y < self.height - 1:
			potentials.append(self.map[x][y + 1])

		for each in potentials:
			if each != None:
				if each.color == color:
					self.map[each.x][each.y] = None
					self.delete_similar_block(each.x, each.y, color)

	def update_block_positions(self):
		while(True):
			moves = 0
			for x in range(self.width):
				for y in range(self.height - 1, 0, -1):
					if self.map[x][y] == None:
						if self.map[x][y-1] != None:
							##  Move the object to the new position and update its y value
							self.map[x][y] = self.map[x][y-1]
							self.map[x][y].y = y
							self.map[x][y-1] = None
							moves += 1
			if moves == 0:
				break

	def create_new_blocks(self):
		num_created = 0
		for x in range(self.width):
			for y in range(self.height):
				if self.map[x][y] == None:
					self.map[x][y] = BlockGame.Block(x,y,random.randrange(self.colors))
					num_created += 1
		return num_created

	def score_calc(self, num_cleared):
		return num_cleared

	class Block:
		def __init__(self, x, y, color):
			self.x = int(x)
			self.y = int(y)
			self.color = int(color)
		
def main():
	pygame.init()
	random.seed()
	
	parser = argparse.ArgumentParser(description='Basic block busting game demo')
	parser.add_argument('-g', '--grid', type=str, default='8x8', help='size of the gameboard, WxH')
	parser.add_argument('-c', '--colors', type=int, default=3, help='number of colors to use')
	parser.add_argument('-m', '--moves', type=int, default=20, help='number of moves allowed in a game')
	parser.add_argument('-s', '--size', type=str, default='320x240', help='size of the game screen')

	args = parser.parse_args()

	grid_width, grid_height = [int(numeric_string) for numeric_string in args.grid.split('x')]
	screen_width, screen_height = [int(numeric_string) for numeric_string in args.size.split('x')]

	x_scalar = math.floor(screen_width / grid_width)
	y_scalar = math.floor(screen_height / grid_height)

	instance = BlockGame(grid_width, grid_height, args.colors, x_scalar, y_scalar)

	screen = pygame.display.set_mode((screen_width, screen_height))

	running = True
	while(running):
		if instance.moves == args.moves:
			print('Final Score:', int(instance.score))
			running=False
			break
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == KEYDOWN and event.key == K_ESCAPE:
				running = False
			elif event.type == MOUSEBUTTONDOWN:
				instance.handle_button_press(pygame.mouse.get_pos())

		instance.draw_board(screen)
		pygame.display.flip()
			
	
if __name__ == "__main__":
	main()
