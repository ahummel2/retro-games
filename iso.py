#!/usr/bin/python

import pygame
from pygame.locals import *
import random
import sys
import math
import time
import threading
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

def rotate(self, angle):
	self.image = pygame.transform.rotate(self.image, angle)

def threaded(fn):
	def wrapper(*args, **kwargs):
		threading.Thread(target=fn, args=args, kwargs=kwargs).start()
	return wrapper

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
	id = 0
	type = 'generic'
	power_need = 5
	power_provided = 0
	water_need = 5
	water_provided = 0
	nimby_effect = 0
	nimby_value = 0
	color = (0,0,0)
	housing = 0
	occupants = 0
	tenants = []
	density = 1
	jobs = 0
	workers = 0
	employees = []
	job_quality = 1
	base_cost = 0
	revenue = 0


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

	def update_water_icon(self):
		if self.water_need > self.water_provided:
			pygame.draw.circle(self.image, (0,0,255), (3,3), 3, 0)
		else:
			pygame.draw.circle(self.image, self.color, (3,3), 3, 0)

	def update_power_icon(self):
		if self.power_need > self.power_provided:
			pygame.draw.circle(self.image, (255,255,0), (6,3), 3, 0)
		else:
			pygame.draw.circle(self.image, self.color, (6,3), 3, 0)

	def remove_self(self):
		pass

class ObjectSelection(Object):
	id = -1
	start_x = 0
	start_y = 0
	end_x = 0
	end_y = 0

	def __init__(self, coords, density=0):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((20,20))
		self.color = (50,50,200)
		#self.image.fill(self.color)
		self.rect = self.image.get_rect()
		self.rect.x = coords[0] * 20
		self.rect.y = coords[1] * 20
		points = [(10,0),(20,10),(10,20),(0,10),(10,0)]
		pygame.draw.polygon(self.image,self.color,points)

		self.start_x = coords[0]
		self.start_y = coords[1]
		self.end_x = coords[0]
		self.end_y = coords[1]

	def update_size(self, coords):
		self.end_x = coords[0]
		self.end_y = coords[1]
		width = abs(self.end_x - self.start_x)
		height = abs(self.end_y - self.start_y)
		self.image = pygame.Surface(((width*20)+20,(height*20)+20))
		self.color = (50,50,200)
		#self.image.fill(self.color)
		self.rect = self.image.get_rect()
		self.rect.x = min(self.start_x, self.end_x) * 20
		self.rect.y = min(self.start_y, self.end_y) * 20
		points = [
			((width + 1) * 10,0),
			((width + 1) * 20,(height + 1) * 10),
			((width + 1) * 10,(height + 1) * 20),
			((0,(height + 1) * 10)),
		    ((width + 1) * 10,0)
		]
		#points = [((width * 20) + 10,0),((width*20)+20,(height*20)+10),((width*20)+10,(height*20)+20),(0,(height*20)+10),((width*20)+10,0)]
		pygame.draw.polygon(self.image,self.color,points)

		self.x = coords[0]
		self.y = coords[1]

	def update_water_icon(self):
		pass
	def update_power_icon(self):
		pass


class Residential(Object):
	id = 1
	type = 'residential'
	nimby_effect = 1
	base_housing = 10
	base_power_need = 5
	base_water_need = 5
	base_cost = 100
	base_max_revenue = 100

	def __init__(self, coords, density):
		(x,y) = coords
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((20,20))
		self.color = (0,255,0)
		#self.image.fill(self.color)
		self.rect = self.image.get_rect()
		self.rect.x = x * 20
		self.rect.y = y * 20

		self.x = x
		self.y = y

		#points = [(x + 5, y),(x + 10,y + 5),(x + 5,y + 10),(x,y + 5),(x + 5,y)]
		points = [(10,0),(20,10),(10,20),(0,10),(10,0)]
		pygame.draw.polygon(self.image,self.color,points)

		self.cost = self.base_cost * density
		self.housing = int(self.base_housing * 1.4 * density)
		self.max_revenue = self.base_max_revenue * 1.3 * density
		self.power_need = self.base_power_need * 1.2 * density
		self.water_need = self.base_water_need * 1.2 * density

	def calculate_revenue(self, tax_rate):
		##  May want to include power and water in this at some point
		#return self.max_revenue * (self.occupants / self.housing) * tax_rate
		##  Doing this for now until I sort out the population and occupancy deal.  Same for com/ind
		return self.max_revenue * tax_rate

	def print_details(self):
		print self.type
		print str(self.occupants) + '/' + str(self.housing) + ' tenants'
		print self.power_provided, self.power_need

	def remove_self(self):
		for guy in self.tenants:
			guy.home = 0

class Commercial(Object):
	id = 2
	type = 'commercial'
	base_power_need = 10
	base_water_need = 3
	nimby_effect = 1
	jobs = 15
	base_cost = 150
	base_max_revenue = 150

	def __init__(self, coords, density):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((20,20))
		self.color = (255,0,255)
		self.image.fill(self.color)
		self.rect = self.image.get_rect()
		self.rect.x = coords[0] * 20
		self.rect.y = coords[1] * 20

		self.x = coords[0]
		self.y = coords[1]

		self.cost = self.base_cost * density
		self.max_revenue = self.base_max_revenue * density
		self.power_need = self.base_power_need * 1.2 * density
		self.water_need = self.base_water_need * 1.2 * density

	def calculate_revenue(self, tax_rate):
		#return self.max_revenue * (self.workers / self.jobs) * tax_rate
		return self.max_revenue * tax_rate

	def print_details(self):
		print self.type
		print str(self.workers) + '/' + str(self.jobs) + ' employees'

	def remove_self(self):
		for guy in self.employees:
			guy.job = 0

class Industrial(Object):
	id = 3
	type = 'industrial'
	power_need = 10
	water_need = 10
	nimby_effect = -2
	jobs = 30
	base_cost = 200
	base_max_revenue = 225

	def __init__(self, coords, density):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((20,20))
		self.color = (255,0,0)
		self.image.fill(self.color)
		self.rect = self.image.get_rect()
		self.rect.x = coords[0] * 20
		self.rect.y = coords[1] * 20

		self.x = coords[0]
		self.y = coords[1]

		self.cost = self.base_cost * density
		self.max_revenue = self.base_max_revenue * density

	def calculate_revenue(self, tax_rate):
		#return self.max_revenue * (self.workers / self.jobs) * tax_rate
		return self.max_revenue * tax_rate

	def print_details(self):
		print self.type
		print str(self.workers) + '/' + str(self.jobs) + ' employees'

	def remove_self(self):
		for guy in self.employees:
			guy.job = 0

class Public(Object):
	id = 4
	type = 'public'
	power_need = 10
	nimby_effect = 2
	jobs = 30
	base_cost = 400
	max_revenue = 0

	def __init__(self, coords, density):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((20,20))
		self.color = (0,0,255)
		self.image.fill(self.color)
		self.rect = self.image.get_rect()
		self.rect.x = coords[0] * 20
		self.rect.y = coords[1] * 20

		self.x = coords[0]
		self.y = coords[1]

		self.cost = self.base_cost * density

	def calculate_revenue(self, tax_rate):
		return -20

	def print_details(self):
		print self.type
		print str(self.workers) + '/' + str(self.jobs) + ' employees'

	def remove_self(self):
		for guy in self.employees:
			guy.job = 0

class PowerPlant(Object):
	id = 5
	type = 'power plant'
	power_need = 0
	nimby_effect = -5
	base_power_generation = 200
	power_usage = 0
	jobs = 40
	base_cost = 2000

	def __init__(self, coords, density):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((20,20))
		self.color = (255,255,255)
		self.image.fill(self.color)
		self.rect = self.image.get_rect()
		self.rect.x = coords[0] * 20
		self.rect.y = coords[1] * 20

		self.x = coords[0]
		self.y = coords[1]

		self.cost = self.base_cost * density
		self.power_generation = self.base_power_generation * density

	def calculate_revenue(self, tax_rate):
		return -100

	def print_details(self):
		print self.type
		print str(self.workers) + '/' + str(self.jobs) + ' employees'

	def remove_self(self):
		for guy in self.employees:
			guy.job = 0

class WaterPlant(Object):
	id = 6
	type = 'water plant'
	water_need = 0
	nimby_effect = -4
	base_water_generation = 150
	water_usage = 0
	jobs = 40
	base_cost = 1000

	def __init__(self, coords, density):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.Surface((20,20))
		self.color = (255,255,255)
		self.image.fill(self.color)
		self.rect = self.image.get_rect()
		self.rect.x = coords[0] * 20
		self.rect.y = coords[1] * 20

		self.x = coords[0]
		self.y = coords[1]

		self.cost = self.base_cost * density
		self.water_generation = self.base_water_generation * density

	def calculate_revenue(self, tax_rate):
		return -60

	def print_details(self):
		print self.type
		print str(self.workers) + '/' + str(self.jobs) + ' employees'

	def remove_self(self):
		for guy in self.employees:
			guy.job = 0

class Road(Object):
	id = 7
	type = 'road'
	power_need = 0
	water_need = 0
	nimby_effect = 0
	usage = 0
	base_capacity = 20
	base_cost = 10
	east = 0
	west = 0
	north = 0
	south = 0

	def __init__(self, coords, density):
		##  Figure out how to properly handle intersections
		pygame.sprite.Sprite.__init__(self)
		self.ss = Spritesheet('sprites/roads.png')
		self.image = pygame.Surface((20,20))
		self.color = (30,30,30)
		self.image.fill(self.color)

		self.rect = self.image.get_rect()
		self.rect.x = coords[0] * 20
		self.rect.y = coords[1] * 20

		self.x = coords[0]
		self.y = coords[1]

		self.cost = self.base_cost * density
		self.capacity = self.base_capacity * density

	def find_connections(self, grid):
		if self.x > 0:
			west = grid[self.x-1][self.y]
			if west != 0:
				if west.id == 7:
					self.west = west
					self.west.east = self
		if self.x < 24:
			east = grid[self.x+1][self.y]
			if east != 0:
				if east.id == 7:
					self.east = east
					self.east.west = self
		if self.y > 0:
			north = grid[self.x][self.y-1]
			if north != 0:
				if north.id == 7:
					self.north = north
					self.north.south = self
		if self.y < 32:
			south = grid[self.x][self.y+1]
			if south != 0:
				if south.id == 7:
					self.south = south
					self.south.north = self

	def remove_self(self):
		if self.west != 0:
			self.west.east = 0
			self.west.update_sprite()
		if self.east != 0:
			self.east.west = 0
			self.east.update_sprite()
		if self.north != 0:
			self.north.south = 0
			self.north.update_sprite()
		if self.south != 0:
			self.south.north = 0
			self.south.update_sprite()

		self.west = 0
		self.east = 0
		self.north = 0
		self.south = 0


	def update_sprite(self):
		##  Need to handle road connections correctly
		#pygame.draw.rect(self.image, self.color, (0, 0, 20, 20))
		#pygame.draw.rect(self.image, (130,130,130), (3, 3, 14, 14))
		#if self.west != 0:
		#    pygame.draw.rect(self.image, (130,130,130), (0, 3, 3, 14))
		#if self.east != 0:
		#    pygame.draw.rect(self.image, (130,130,130), (17, 3, 3, 14))
		#if self.north != 0:
		#    pygame.draw.rect(self.image, (130,130,130), (3, 0, 14, 3))
		#if self.south != 0:
		#    pygame.draw.rect(self.image, (130,130,130), (3, 17, 14, 3))
		#pygame.display.update()
		if self.west == 0 and self.east == 0 and self.north == 0 and self.south == 0:
			self.image = self.ss.image_at((100, 60, 20, 20))
		if self.west == 0 and self.east == 0 and self.north == 0 and self.south != 0:
			self.image = self.ss.image_at((20, 40, 20, 20))
		if self.west == 0 and self.east == 0 and self.north != 0 and self.south == 0:
			self.image = self.ss.image_at((0, 60, 20, 20))
		if self.west == 0 and self.east == 0 and self.north != 0 and self.south != 0:
			self.image = self.ss.image_at((120, 0, 20, 20))
		if self.west == 0 and self.east != 0 and self.north == 0 and self.south == 0:
			self.image = self.ss.image_at((100, 0, 20, 20))
		if self.west == 0 and self.east != 0 and self.north == 0 and self.south != 0:
			self.image = self.ss.image_at((0, 0, 20, 20))
		if self.west == 0 and self.east != 0 and self.north != 0 and self.south == 0:
			self.image = self.ss.image_at((120, 20, 20, 20))
		if self.west == 0 and self.east != 0 and self.north != 0 and self.south != 0:
			self.image = self.ss.image_at((100, 20, 20, 20))
		if self.west != 0 and self.east == 0 and self.north == 0 and self.south == 0:
			self.image = self.ss.image_at((80, 20, 20, 20))
		if self.west != 0 and self.east == 0 and self.north == 0 and self.south != 0:
			self.image = self.ss.image_at((40, 40, 20, 20))
		if self.west != 0 and self.east == 0 and self.north != 0 and self.south == 0:
			self.image = self.ss.image_at((140, 0, 20, 20))
		if self.west != 0 and self.east == 0 and self.north != 0 and self.south != 0:
			self.image = self.ss.image_at((80, 40, 20, 20))
		if self.west != 0 and self.east != 0 and self.north == 0 and self.south == 0:
			self.image = self.ss.image_at((80, 60, 20, 20))
		if self.west != 0 and self.east != 0 and self.north == 0 and self.south != 0:
			self.image = self.ss.image_at((20, 0, 20, 20))
		if self.west != 0 and self.east != 0 and self.north != 0 and self.south == 0:
			self.image = self.ss.image_at((140, 20, 20, 20))
		if self.west != 0 and self.east != 0 and self.north != 0 and self.south != 0:
			self.image = self.ss.image_at((100, 40, 20, 20))
		pygame.display.update()

	def update_connections(self):
		if self.west != 0:
			self.west.update_sprite()
		if self.east != 0:
			self.east.update_sprite()
		if self.north != 0:
			self.north.update_sprite()
		if self.south != 0:
			self.south.update_sprite()


	##  Make some overrides to the original functions, these aren't needed for roads
	def update_water_icon(self):
		pass
	def update_power_icon(self):
		pass



	def print_details(self):
		print 'Connections: ', self.west, self.east, self.north, self.south
		print 'Usage: ' + str(self.usage) + '/' + str(self.capacity)

class Person():
	age = 0
	education = 0
	home = 0
	job = 0
	in_workforce = False
	path_to_work = False

	def __init__(self, age, education):
		if age:
			self.age = age
		else:
			self.age = 18
		if education:
			self.education = education
		else:
			self.education = 12
		self.in_workforce = True

class Game():
	def __init__(self):
		pygame.init()

		parser = OptionParser()
		parser.add_option('-l', '--load', dest='load_save', default=False, help='Load a save file')
		parser.add_option('-r', '--resolution', dest='resolution', default='640x495', help='Preferred resolution')
		(self.options, self.args) = parser.parse_args()

		res = self.options.resolution.split('x')
		global res_x
		global res_y
		(res_x, res_y) = int(res[0]), int(res[1])
		self.screen = pygame.display.set_mode((res_x,res_y),0,32)
		pygame.display.set_caption("Sim-City clone")

		self.background = pygame.Surface((res_x,res_y))
		self.background.fill((0,0,0))
		self.screen.blit(self.background, (0,0))
		pygame.display.update()

		global x_max
		global y_max
		x_max = math.trunc(res_x/20)
		y_max = math.trunc((res_y - 15)/20)
		self.grid = [[0 for x in range(y_max)] for x in range(x_max)]

		self.objects = pygame.sprite.RenderUpdates()
		self.people = []

		self.date = date(1970, 1, 1)
		self.clock = pygame.time.Clock()
		self.type_selection = 0
		self.balance = 20000
		self.tax_r = 0.07
		self.tax_c = 0.07
		self.tax_i = 0.10
		self.current_population = 0
		self.housing_limit = 0
		self.current_employed = 0
		self.job_limit = 0

		##  Timer for power usage calculation
		self.POWERCALC = pygame.USEREVENT + 1
		self.NIMBYCALC = pygame.USEREVENT + 2
		self.STATUSCALC = pygame.USEREVENT + 3
		self.REVENUECALC = pygame.USEREVENT + 4
		self.FINDJOBS = pygame.USEREVENT + 5
		self.DATECHANGE = pygame.USEREVENT + 6
		pygame.time.set_timer(self.POWERCALC, 5000)
		pygame.time.set_timer(self.NIMBYCALC, 6000)
		pygame.time.set_timer(self.STATUSCALC, 3000)
		pygame.time.set_timer(self.REVENUECALC, 10000)
		pygame.time.set_timer(self.FINDJOBS, 10000)
		pygame.time.set_timer(self.DATECHANGE, 4000)

		self.font = pygame.font.SysFont('monospace', 15)
		self.status_bar_update()
		self.object_selection = 0
		self.density_selection = 1
		self.mouseDown = False

		if self.options.load_save:
			self.load_game(self.options.load_save)

		self.game_running = True
		self.background_thread = threading.Thread(target=self.background_work)
		self.background_thread.start()
		#self.background_work()

	def save_game(self):
		file = open('./saves/saved-game.dat', 'w')
		line = str(self.current_population) + ':' + str(self.current_employed) + ':' + str(self.balance) + ':'
		line += self.date.isoformat() + ':32:24'
		line += '\n'
		file.write(line)
		for row in self.grid:
			line = ''
			for thing in row:
				if thing == 0:
					line += '0:'
				else:
					line += str(thing.id) + ':'
			line += '\n'
			file.write(line)
		file.close()
		print 'Saved game'

	def load_game(self, file_name='./saves/saved-game.dat'):
		file = open(file_name, 'r')
		details = file.readline()
		(pop, jobs, balance, date_value, rows, cols) = details.split(':')
		for i in range(0, int(rows)):
			row = file.readline()
			values = row.split(':')
			for j in range(0, int(cols)):
				if int(values[j]) == 0:
					self.grid[i][j] = 0
				else:
					object = self.get_new_object(int(values[j]), (i, j))
					self.grid[i][j] = object
					self.add_object(object, (i, j))
		file.close()
		self.balance = float(balance)
		str = date_value.split('-')
		self.date = date(int(str[0]),int(str[1]),int(str[2]))
		self.find_jobs()
		self.status_bar_update()


	def run(self):
		while self.game_running:
			for event in pygame.event.get():
				if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
					self.game_running = False
					return
				if event.type == KEYDOWN:
					self.handle_keyboard_inputs(event)

				## Improved method for placing objects, should show a selector, draggable over an area
				if event.type == pygame.MOUSEBUTTONDOWN or self.mouseDown:
					self.mouseDown = True
					coords = pygame.mouse.get_pos()
					real_coords = self.convertCoords(coords)
					(x, y) = self.grid_coords(real_coords)
					if self.object_selection:
						self.object_selection.update_size((x,y))
					else:
						self.object_selection = ObjectSelection((x,y))
						self.add_object(self.object_selection, (x,y))


				if event.type == pygame.MOUSEBUTTONUP:
					self.mouseDown = False
					x1 = min(self.object_selection.start_x,self.object_selection.end_x)
					x2 = max(self.object_selection.start_x,self.object_selection.end_x) + 1
					y1 = min(self.object_selection.start_y,self.object_selection.end_y)
					y2 = max(self.object_selection.start_y,self.object_selection.end_y) + 1

					for x in range(x1,x2):
						for y in range(y1,y2):
							self.objects.remove(self.object_selection)
							self.object_selection = 0
					##  Maybe do some check here so that i don't place a big-ass grid of roads, no one needs that
					if (self.can_place_object((x1,y1), (x2,y2))):
						for x in range(x1,x2):
							for y in range(y1,y2):
								object = self.get_new_object(self.type_selection, (x,y), self.density_selection)
								if object != 0:
									self.add_object(object, (x,y))
					else:
						for case in switch(self.type_selection):
							if case(0):
								##  Just want to get details about the object here
								thing = self.grid[x][y]
								thing.print_details()
								break
							if case(10):
								for x in range(x1,x2):
									for y in range(y1,y2):
										self.remove_object((x, y))

				#if event.type == pygame.MOUSEBUTTONUP:
				#    coords = pygame.mouse.get_pos()
				#    real_coords = self.convertCoords(coords)
				#    (x, y) = self.grid_coords(real_coords)
				#    if (self.can_place_object((x, y))):
				#        object = self.get_new_object(self.type_selection, (x, y))
				#        if object != 0:
				#            self.add_object(object, (x, y))
				#    else:
				#        for case in switch(self.type_selection):
				#            if case(0):
				#                ##  Just want to get details about the object here
				#                thing = self.grid[x][y]
				#                thing.print_details()

				#                break
				#            if case(10):
				#                self.remove_object((x, y))

				if event.type == self.POWERCALC:
					self.power_calculation()
					self.water_calculation()
				if event.type == self.NIMBYCALC:
					self.nimby_calculation()
				if event.type == self.STATUSCALC:
					self.status_bar_update()
				if event.type == self.REVENUECALC:
					self.calculate_revenue()
				#if event.type == self.FINDJOBS:
				#	self.find_jobs()
				#	self.set_job_paths()
				if event.type == self.DATECHANGE:
					self.update_date()

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

	@threaded
	def background_work(self):
		try:
			while(self.game_running):
				#print 'Doing background work'
				self.find_jobs()
				self.set_job_paths()
				time.sleep(1)
		except Exception as e:
			print 'Background thread failed, exiting'
			print e
			self.game_running = False
			exit(-1)

	def get_new_object(self, id, coords, density=1):
		for case in switch(id):
			if case(1):
				object = Residential(coords, density)
				break
			if case(2):
				object = Commercial(coords, density)
				break
			if case(3):
				object = Industrial(coords, density)
				break
			if case(4):
				object = Public(coords, density)
				break
			if case(5):
				object = PowerPlant(coords, density)
				break
			if case(6):
				object = WaterPlant(coords, density)
				break
			if case(7):
				object = Road(coords, density)
				object.find_connections(self.grid)
				object.update_sprite()
				object.update_connections()
				break
			else:
				object = 0
		return object

	def update_date(self):
		delta = timedelta(days=1)
		self.date += delta
		self.status_bar_update()

	def add_object(self, object, coords):
		(x, y) = coords
		self.objects.add(object)
		if object.id != -1:
			self.grid[x][y] = object
			self.balance -= object.cost
			self.status_bar_update()

	def remove_object(self, coords):
		(x, y) = coords
		object = self.grid[x][y]
		if object == 0:
			return False
		else:
			object.remove_self()
			self.grid[x][y] = 0
			self.objects.remove(object)
			return True

	def convertCoords(self, coords):
		real_x = round_down(coords[0],20)
		real_y = round_down(coords[1],20)
		return (real_x, real_y)

	def grid_coords(self, coords):
		x = coords[0] / 20
		y = coords[1] / 20
		return (x, y)

	def can_place_object(self, coords1, coords2=None):
		global x_max
		global y_max
		if coords1 != coords2:
			for x in range(coords1[0],coords2[0]):
				for y in range(coords1[1],coords2[1]):
					if x >= x_max or y >= y_max:
						print 'Grid selection outside of range'
						return False
					else:
						value = self.grid[x][y]
						if value != 0:
							return False
			return True
		else:
			(x, y) = coords1
			value = self.grid[x][y]
			if value == 0:
				return True
			return False

	def status_bar_update(self):
		global x_max
		global y_max
		pygame.draw.rect(self.screen, (100,100,100), (0,20 * y_max,20 * x_max,15),0)

		pop_limit = 0
		job_limit = 0
		for place in self.objects.sprites():
			pop_limit += place.housing
			job_limit += place.jobs

		pop = 0
		jobs = 0
		for guy in self.people:
			pop += 1
			if guy.job != 0:
				jobs += 1

		self.housing_limit = pop_limit
		self.current_population = pop
		self.job_limit = job_limit
		self.current_employed = jobs

		#self.status_bar.update_values(self.screen, pop_limit, job_limit)
		self.status_bar = 'Pop: ' + str(self.current_population) + '/' + str(self.housing_limit) + '    '
		self.status_bar += 'Jobs: ' + str(self.current_employed) + '/' + str(self.job_limit) + '    '
		self.status_bar += 'Balance: $' + str(self.balance) + '    '
		self.status_bar += 'Date: ' + self.date.isoformat()
		self.status_bar_container = self.font.render(self.status_bar, 1, (255,255,255), (100,100,100))
		self.screen.blit(self.status_bar_container, (5,20 * y_max))
		pygame.display.update()

	def find_jobs(self):
		##  Fuck if I know what I'm doing here
		##  Rehouse homeless people with jobs
		for guy in self.people:
			if guy.home == 0 and guy.job != 0:
				for place in self.objects.sprites():
					if place.housing - place.occupants > 0:
						##  Maybe do some distance calc here to find the closest place
						place.occupants += 1
						place.tenants.append(guy)
						guy.home = place
						break
		##  Reemploy jobless people with homes
		for guy in self.people:
			if guy.home != 0 and guy.job == 0:
				for place in self.objects.sprites():
					if place.jobs - place.workers > 0:
						place.workers += 1
						place.employees.append(guy)
						guy.job = place
						break
		##  Do both for the really poor bastards
		for guy in self.people:
			if guy.home == 0 and guy.job == 0:
				for place in self.objects.sprites():
					if place.jobs - place.workers > 0:
						place.workers += 1
						place.employees.append(guy)
						guy.job = place
						break
				if guy.job != 0:
					for place in self.objects.sprites():
						if place.housing - place.occupants > 0:
							##  Maybe do some distance calc here to find the closest place
							place.occupants += 1
							place.tenants.append(guy)
							guy.home = place
							break

		##  Then find out how many new people can be brought in
		##  Find out min(open housing, open jobs)
		open_housing = 0
		open_jobs = 0
		for each in self.objects.sprites():
			open_housing += each.housing - each.occupants
			open_jobs += each.jobs - each.workers

		new_people = min(open_housing, open_jobs)

		#print 'Need to create ' + str(new_people) + ' people objects'
		for i in range(0,new_people):
			guy = Person(18, 1)
			self.people.append(guy)
			##  Find job for this jerk
			for place in self.objects.sprites():
				if place.jobs - place.workers > 0:
					place.workers += 1
					place.employees.append(guy)
					guy.job = place
					break
			## Find place for this jerk to live
			for place in self.objects.sprites():
				if place.housing - place.occupants > 0:
					##  Maybe do some distance calc here to find the closest place
					place.occupants += 1
					place.tenants.append(guy)
					guy.home = place
					break
		self.status_bar_update()

	def set_job_paths(self):
		##  Find closest road objects to the guy's home and work place
		for guy in self.people:
			if guy.home != 0 and guy.job != 0:
				(home_x, home_y) = (guy.home.x, guy.home.y)
				(job_x, job_y) = (guy.job.x, guy.job.y)
				distance = get_distance((home_x,home_y), (job_x,job_y))
				if distance < 3:
					##  Don't need to compute a path, lucky fucker is walking to work
					guy.path = -1
					break

				closest = {}
				result = 0
				for i in range(max(0,home_x - 3), min(31, home_x + 3)):
					for j in range(max(0,home_y - 3), min(23, home_y + 3)):
						if self.grid[i][j] != 0:
							if self.grid[i][j].id == 7:
								distance = get_distance((home_x,home_y),(self.grid[i][j].x,self.grid[i][j].y))
								while distance in closest.keys():
									distance += 0.01
								closest[distance] = self.grid[i][j]
				try:
					home_road = closest[sorted(closest.keys())[0]]
				except:
					##  No road, can't start a path thing
					guy.path_to_work = result
					break
				closest = {}
				for i in range(max(0,job_x - 3), min(31, job_x + 3)):
					for j in range(max(0,job_y - 3), min(23, job_y + 3)):
						if self.grid[i][j] != 0:
							if self.grid[i][j].id == 7:
								distance = get_distance((job_x,job_y),(self.grid[i][j].x,self.grid[i][j].y))
								while distance in closest.keys():
									distance += 0.01
								closest[distance] = self.grid[i][j]
				job_road = closest[sorted(closest.keys())[0]]

				##  Do some pathfinding work here
				result = self.a_star_path((home_road.x,home_road.y), (job_road.x,job_road.y))
				guy.path_to_work = result

		self.find_road_usage()


	def a_star_path(self, start, goal):
		##  AStar method for finding a path
		neighbors = [(0,1),(0,-1),(1,0),(-1,0)]

		close_set = set()
		open_set = set()
		came_from = {}
		gscore = {start:0}
		fscore = {start:heuristic(start, goal)}
		oheap = []

		open_set.add(start)
		heappush(oheap, (fscore[start], start))

		while len(open_set):
			current = heappop(oheap)[1]

			if current == goal:
				data = []
				while current in came_from:
					data.append(current)
					current = came_from[current]
				return data

			open_set.discard(current)
			close_set.add(current)
			for i, j in neighbors:
				neighbor = current[0] + i, current[1] + j
				tentative_g_score = gscore[current] + heuristic(current, neighbor)
				if 0 <= neighbor[0] < 31:
					if 0 <= neighbor[1] < 23:
						if self.grid[neighbor[0]][neighbor[1]] != 0:
							if self.grid[neighbor[0]][neighbor[1]].id != 7:
								continue
						else:
							continue
					else:
						# array bound y walls
						continue
				else:
					# array bound x walls
					continue

				if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
					continue

				if neighbor not in open_set or tentative_g_score < gscore.get(neighbor, 0):
					came_from[neighbor] = current
					gscore[neighbor] = tentative_g_score
					fscore[neighbor] = tentative_g_score + heuristic(neighbor, goal)
					open_set.add(neighbor)
					heappush(oheap, (fscore[neighbor], neighbor))

		##  Got to this point, data should be empty or hold the path
		return False

	def find_road_usage(self):
		##  Only want to iterate over the entire population once if I have to
		##  So lets iterate over the roads first, reset their usage, and then
		##  Add to it for each guy with a job_path
		for row in self.grid:
			for cell in row:
				if cell != 0:
					if cell.id == 7:
						cell.usage = 0

		for guy in self.people:
			if guy.path_to_work:
				for (x,y) in guy.path_to_work:
					self.grid[x][y].usage += 1


	def power_calculation(self):
		plants = []
		for row in self.grid:
			for cell in row:
				if cell != 0:
					cell.power_provided = 0
					if cell.id == 5:
						plants.append(cell)

		for plant in plants:
			plant.power_usage = 0
			objects = {}
			for row in self.grid:
				for cell in row:
					if cell != 0:
						if cell.id != 5:
							distance = get_distance((plant.x,plant.y), (cell.x, cell.y))
							while distance in objects.keys():
								distance += 0.01
							objects[distance] = cell

			for key in sorted(objects.keys()):
				thing = objects[key]
				need = thing.power_need - thing.power_provided
				available = plant.power_generation - plant.power_usage
				value = min(need, available)
				plant.power_usage += value
				thing.power_provided += value

		for row in self.grid:
			for thing in row:
				if thing != 0:
					thing.update_power_icon()

	def water_calculation(self):
		plants = []
		for row in self.grid:
			for cell in row:
				if cell != 0:
					cell.water_provided = 0
					if cell.id == 6:
						plants.append(cell)

		for plant in plants:
			plant.water_usage = 0
			objects = {}
			for row in self.grid:
				for cell in row:
					if cell != 0:
						if cell.id != 6:
							distance = get_distance((plant.x,plant.y), (cell.x,cell.y))
							while distance in objects.keys():
								distance += 0.01
							objects[distance] = cell

			for key in sorted(objects.keys()):
				thing = objects[key]
				need = thing.water_need - thing.water_provided
				available = plant.water_generation - plant.water_usage
				value = min(need, available)
				plant.water_usage += value
				thing.water_provided += value

		for row in self.grid:
			for thing in row:
				if thing != 0:
					thing.update_water_icon()

	def nimby_calculation(self):
		objects = []
		for row in self.grid:
			for cell in row:
				if cell != 0:
					objects.append(cell)

		for thing1 in objects:
			thing1.nimby_value = 0
			for thing2 in objects:
				if thing1 != thing2:
					distance = get_distance((thing1.x,thing1.y), (thing2.x,thing2.y))
					if distance < 5:
						thing1.nimby_value += thing2.nimby_effect

	def calculate_revenue(self):
		revenue = 0
		for row in self.grid:
			for thing in row:
				if thing != 0:
					for case in switch(thing.id):
						if case(1):
							revenue += thing.calculate_revenue(self.tax_r)
							break
						if case(2):
							revenue += thing.calculate_revenue(self.tax_r)
							break
						if case(3):
							revenue += thing.calculate_revenue(self.tax_r)
							break

		self.balance += revenue
		self.status_bar_update()

	def handle_keyboard_inputs(self, event):
		##  Will need reworking at some point, but just to get things started this'll do
		for case in switch(event.key):
			if case(K_1):
				if self.type_selection == 1:
					if self.density_selection < 3:
						self.density_selection += 1
					else:
						self.density_selection = 1
					print 'Density: ' + str(self.density_selection)
				else:
					self.type_selection = 1
					self.density_selection = 1
					print 'Selected: Residential'
				break
			if case(K_2):
				if self.type_selection == 2:
					if self.density_selection < 3:
						self.density_selection += 1
					else:
						self.density_selection = 1
					print 'Density: ' + str(self.density_selection)
				else:
					self.type_selection = 2
					self.density_selection = 1
					print 'Selected: Commercial'
				break
			if case(K_3):
				if self.type_selection == 3:
					if self.density_selection < 3:
						self.density_selection += 1
					else:
						self.density_selection = 1
					print 'Density: ' + str(self.density_selection)
				else:
					self.type_selection = 3
					self.density_selection = 1
					print 'Selected: Industrial'
				break
			if case(K_4):
				if self.type_selection == 4:
					if self.density_selection < 3:
						self.density_selection += 1
					else:
						self.density_selection = 1
					print 'Density: ' + str(self.density_selection)
				else:
					self.type_selection = 4
					self.density_selection = 1
					print 'Selected: Public'
				break

			if case(K_5):
				if self.type_selection == 5:
					if self.density_selection < 3:
						self.density_selection += 1
					else:
						self.density_selection = 1
					print 'Density: ' + str(self.density_selection)
				else:
					self.type_selection = 5
					self.density_selection = 1
					print 'Selected: Power Plant'
				break

			if case(K_6):
				if self.type_selection == 6:
					if self.density_selection < 3:
						self.density_selection += 1
					else:
						self.density_selection = 1
					print 'Density: ' + str(self.density_selection)
				else:
					self.type_selection = 6
					self.density_selection = 1
					print 'Selected: Water Plant'
				break

			if case(K_7):
				if self.type_selection == 7:
					if self.density_selection < 3:
						self.density_selection += 1
					else:
						self.density_selection = 1
					print 'Density: ' + str(self.density_selection)
				else:
					self.type_selection = 7
					self.density_selection = 1
					print 'Selected: Road'
				break

			if case(K_8):
				self.type_selection = 8
				print 'Selected: 8'
				break
			if case(K_9):
				self.type_selection = 9
				print 'Selected: 9'
				break
			if case(K_b):
				self.type_selection = 10
				print 'Selected: Bulldozer'
				break
			if case(K_l):
				if self.options.load_save:
					self.load_game(self.options.load_save)
				else:
					self.load_game()
				break
			if case(K_s):
				self.save_game()
				break
			if case(K_SPACE):
				self.type_selection = 0
				print 'Selected: None'
				break



if __name__ == '__main__':
	game = Game()
	try:
		game.run()
	except Exception as e:
		game.game_running = False
		print e
		print sys.exc_info()[0]
