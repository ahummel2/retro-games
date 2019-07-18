#!/usr/bin/python

import pygame
from pygame.locals import *
import random
import sys
import math
import time
from heapq import *
from optparse import OptionParser
from datetime import date, timedelta

random.seed()
x_max = 0
res_x = 0
y_max = 0
res_y = 0

class switch(object):
	def __init__(self, value):
		self.value = value
		self.fall = False

	def __iter__(self):
		"""Return the match method once, then stop"""
		yield self.match
		raise StopIteration

	def match(self, *args):
		"""Indicate whether or not to enter a case suite"""
		if self.fall or not args:
			return True
		elif self.value in args: # changed for v1.5, see below
			self.fall = True
			return True
		else:
			return False

def round_down(num, divisor):
	return num - (num%divisor)

def heuristic(a, b):
	"""calculates the H cost using the Manhattan Method"""
	return 10*(abs(a[0] - b[0]) + abs(a[1] - b[1]))

def get_distance(coord1, coord2):
	diff_x = coord1[0] - coord2[0]
	diff_y = coord1[1] - coord2[1]
	return math.sqrt(math.pow(diff_x,2) + math.pow(diff_y,2))

class Spritesheet(object):
	def __init__(self, filename):
		try:
			self.sheet = pygame.image.load(filename).convert()
		except pygame.error, message:
			print 'Unable to load spritesheet image:', filename
			raise SystemExit, message
	# Load a specific image from a specific rectangle
	def image_at(self, rectangle, colorkey = None):
		"Loads image from x,y,x+offset,y+offset"
		rect = pygame.Rect(rectangle)
		image = pygame.Surface(rect.size).convert()
		image.blit(self.sheet, (0, 0), rect)
		if colorkey is not None:
			if colorkey is -1:
				colorkey = image.get_at((0,0))
			image.set_colorkey(colorkey, pygame.RLEACCEL)
		return image
	# Load a whole bunch of images and return them as a list
	def images_at(self, rects, colorkey = None):
		"Loads multiple images, supply a list of coordinates"
		return [self.image_at(rect, colorkey) for rect in rects]
	# Load a whole strip of images
	def load_strip(self, rect, image_count, colorkey = None):
		"Loads a strip of images and returns them as a list"
		tups = [(rect[0]+rect[2]*x, rect[1], rect[2], rect[3])
				for x in range(image_count)]
		return self.images_at(tups, colorkey)

class Object(pygame.sprite.Sprite):

	def __init__(self, coords):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((20,20))
		self.color = (random.randrange(0,255),random.randrange(0,255),random.randrange(0,255))
		self.image.fill(self.color)
		self.rect = self.image.get_rect()
		self.rect.x = coords[0] * 20
		self.rect.y = coords[1] * 20

		self.x = coords[0]
		self.y = coords[1]

class box(Object):
	def __init__(self, coords):
		self.id = 1
		pygame.sprite.Sprite.__init__(self)
		self.ss = Spritesheet('sprites/box.png')
		self.image = self.ss.image_at((0,0,40,40))
		self.width = 40
		self.height = 40
		self.rect = self.image.get_rect()
		self.rect.x = coords[0]
		self.rect.y = coords[1]

		self.x = coords[0]
		self.y = coords[1]

class cat(Object):
	def __init__(self, coords):
		self.id = 2
		self.speed = 2
		pygame.sprite.Sprite.__init__(self)
		self.ss = Spritesheet('sprites/cat.png')
		self.image = self.ss.image_at((44,126,14,26))
		self.width = 14
		self.height = 26
		self.rect = self.image.get_rect()
		self.rect.x = coords[0]
		self.rect.y = coords[1]

		self.x = coords[0]
		self.y = coords[1]

class Game():
	def __init__(self):
		pygame.init()

		parser = OptionParser()
		parser.add_option('-r', '--resolution', dest='resolution', default='300x420', help='Preferred resolution')
		(self.options, self.args) = parser.parse_args()

		res = self.options.resolution.split('x')
		global res_x
		global res_y
		(res_x, res_y) = int(res[0]), int(res[1])
		self.screen = pygame.display.set_mode((res_x,res_y),0,32)
		pygame.display.set_caption("Cat in a Box")

		self.background = pygame.Surface((res_x,res_y))
		self.background.fill((0,0,0))
		self.screen.blit(self.background, (0,0))
		pygame.display.update()

		self.objects = pygame.sprite.OrderedUpdates()

		object = self.get_new_object(1, (100,100))
		self.objects.add(object)

		object = self.get_new_object(2, (200,200))
		self.objects.add(object)

		self.font = pygame.font.SysFont('monospace', 15)
		self.mouseDragging = False
		self.game_running = True
		self.clock = pygame.time.Clock()
		self.clickedObject = -1
		self.clickDiffX = 0
		self.clickDiffY = 0

	def get_new_object(self, id, coords):
		for case in switch(id):
			if case(1):
				object = box(coords)
				break
			if case(2):
				object = cat(coords)
				break
			else:
				object = 0
		return object

	def add_object(self, object, coords):
		(x, y) = coords
		self.objects.add(object)
		if object.id != -1:
			self.grid[x][y] = object
			self.balance -= object.cost
			self.status_bar_update()

	def run(self):
		while self.game_running:
			for event in pygame.event.get():
				if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
					self.game_running = False
					return
				if event.type == KEYDOWN:
					for case in switch(event.key):
						if case(K_p):
							for thing in self.objects:
								print thing.id,thing.x,thing.y
						if case(K_s):
							print self.mouseDragging, self.clickedObject

				## Improved method for placing objects, should show a selector, draggable over an area
				if event.type == pygame.MOUSEBUTTONDOWN and self.mouseDragging == False:
					coords = pygame.mouse.get_pos()
					for thing in self.objects:

						if thing.rect.x < coords[0] < (thing.x + thing.width):
							if thing.y < coords[1] < (thing.y + thing.height):
								print 'Clicked on object' + str(thing.id)
								self.clickedObject = thing.id
								self.clickDiffX = coords[0] - thing.x
								self.clickDiffY = coords[1] - thing.y
								self.mouseDragging = True

				if self.mouseDragging == True:
					for thing in self.objects:
						if self.clickedObject == thing.id and thing.id == 2:
							coords = pygame.mouse.get_pos()
							new_x = coords[0] - self.clickDiffX
							new_y = coords[1] - self.clickDiffY
							self.objects.remove(thing)

							object = self.get_new_object(2, (new_x,new_y))
							self.objects.add(object)


				if event.type == pygame.MOUSEBUTTONUP:
					self.mouseDragging = False
					self.clickedObject = -1

			if self.mouseDragging == False:
				##  Check if cat is out of the box
				for thing in self.objects:
					if thing.id == 1:
						box = thing
					elif thing.id == 2:
						cat = thing
				if cat.x < box.x + 4:
					cat.x += cat.speed
				if (cat.x + cat.width) > (box.x + box.width - 4):
					cat.x -= cat.speed

				if cat.y < box.y + 7:
					cat.y += cat.speed
				if (cat.y + cat.height) > (box.y + box.height - 4):
					cat.y -= cat.speed

				new_x = cat.x
				new_y = cat.y

				self.objects.remove(cat)

				object = self.get_new_object(2, (new_x,new_y))
				self.objects.add(object)

			# clear sprites
			self.objects.clear(self.screen, self.background)

			# update sprites
			for sprite in self.objects:
				sprite.update()

			# redraw sprites
			dirty = self.objects.draw(self.screen)
			pygame.display.update(dirty)

			# maintain frame rate
			self.clock.tick(30)

if __name__ == '__main__':
	game = Game()
	try:
		game.run()
	except Exception as e:
		game.game_running = False
		print e
		print sys.exc_info()[0]