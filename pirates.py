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

##	max_crew, hull, speed, turning_radius, storage, cannons_per_side
ship_values = [[5,10,3,10,100,10,10,1,'sprites/pirate-ship.png']]

class PirateGame:
	def __init__(self):
		self.running = True
		self.islands = []
		self.ships = []
		self.cannonballs = []
		self.user_ship = Ship()
		self.ships.append(self.user_ship)
		
		self.ui_elements = []
		ui_sail = UI_element((0.90,0.50), (0.10,0.90), 'vertical', ((200,150,200), (255,220,100)), 'self.user_ship.sail')
		self.ui_elements.append(ui_sail)
		
		self.initiate_world(1200,600)
	
	def initiate_world(self, x_max, y_max):
		port = Island(10, 0, (random.randrange(x_max), random.randrange(y_max)), 0)
		self.islands.append(port)
		for i in range(5):
			##	should do some checks to make sure random x/y arent overlapping
			atoll = Island(6, 500, (random.randrange(x_max), random.randrange(y_max)), 1)
			self.islands.append(atoll)
			
	def objects_to_draw(self):
		objects = self.islands + self.ships + self.cannonballs + self.ui_elements
		return objects
			
	def draw_screen(self, screen):
		screen.fill((130,130,130))
		objects = self.objects_to_draw()
		for each in objects:
			if hasattr(each, 'image'):
				screen.blit(each.image, each.rect)
			else:
				each.draw_me()
		return True
	
	def load_file(self, path):
		print(path)
	
	def rotate_wheel(self, object, angle):
		object.wheel += angle
		if object.wheel >= 2 * object.turning_radius:
			object.wheel = 2 * object.turning_radius
		if object.wheel <= -2 * object.turning_radius:
			object.wheel = -2 * object.turning_radius
	
	def rotate_ship(self, object):
		x, y = object.rect.center
		angle = (object.dir + object.wheel) % 360
		object.image = pygame.transform.rotate(object.sprite, angle)
		object.rect = object.image.get_rect()
		object.rect.center = (x, y)
		angle = (object.dir + object.wheel) % 360
		object.dir = angle
	
	def fire_cannons(self, ship, offset):
		x, y = ship.rect.center
		angle = (ship.dir + offset) % 360
		for each in range(ship.cannons_per_side):
			new = Cannonball(angle, ship.cannon_speed, ship.cannon_ticks, (x, y))
			self.cannonballs.append(new)
	
	def process_event(self, event):
		if event == 'EXIT' or event == K_ESCAPE:
			self.running = False
		if event == K_q:
			self.rotate_wheel(self.user_ship, 2)
		if event == K_e:
			self.rotate_wheel(self.user_ship, -2)
		if event == K_z:
			self.fire_cannons(self.user_ship, 90)
		if event == K_c:
			self.fire_cannons(self.user_ship, -90)
		else:
			pass
		return True
	
	def update_ships(self):
		##	this should process the movements of ships and i guess any cannonballs
		#print(self.user_ship.dir, self.user_ship.wheel)
		for ship in self.ships:
			self.rotate_ship(ship)
	
	def update_cannonballs(self):
		if len(self.cannonballs) > 0:
			balls_copy = self.cannonballs
			for each in balls_copy:
				each.update_position()
				if each.ticks > each.max_ticks:
					self.cannonballs.remove(each)
				
				##	Need to check for collisions here, except for with the ship the cannonball was fired from
	
	def handle_mouse_press(self, pos):
		for each in self.ui_elements:
			if each.rect.collidepoint(pos):
				each.update(pos)
	
	def get_state(self):
		return self.running

class Ship:
	def __init__(self, ship_type=0):
		self.load_ship_stats(ship_type)
	
	def load_ship_stats(self, type):
		self.max_crew = ship_values[type][0]
		self.hull = ship_values[type][1]
		self.speed = ship_values[type][2]
		self.turning_radius = ship_values[type][3]
		self.storage = ship_values[type][4]
		self.cannon_speed = ship_values[type][5]
		self.cannon_ticks = ship_values[type][6]
		self.cannons_per_side = ship_values[type][7]
		
		self.sprite = pygame.image.load(ship_values[type][8]).convert_alpha()
		self.image = self.sprite
		self.dir = 0
		self.wheel = 0
		self.rect = self.image.get_rect()
		self.rect.center = (200,200)

class Cannonball:
	def __init__(self, dir, speed, max_ticks, pos):
		self.dir = dir
		self.speed = speed
		self.ticks = 0
		self.max_ticks = max_ticks
		self.sprite = pygame.image.load('sprites/cannonball.png').convert_alpha()
		self.image = self.sprite
		self.rect = self.image.get_rect()
		self.rect.center = (pos)
	
	def update_position(self):
		x, y = self.rect.center
		y -= math.sin(math.radians(self.dir)) * self.speed
		x += math.cos(math.radians(self.dir)) * self.speed
		self.rect.center = (x, y)
		self.ticks += 1

class Island:
	def __init__(self, size, time, pos, type):
		self.size = size
		self.time = time
		self.type = type
		self.pos = pos
		self.sprite = pygame.image.load('sprites/fish_school.jpg').convert_alpha()
		self.image = self.sprite
		self.rect = self.image.get_rect()
		self.rect.center = self.pos

class UI_element:
	def __init__(self, coords, sizes, type, colors, variable):
		##	coords are the rect center, sizes are the horizontal and vertical values
		##	all represented as percentages of screen size
		self.coords = coords
		self.sizes = sizes
		self.type = type
		self.colors = colors
		self.variable = variable
		
		ref = screen.get_size()
		self.bground = pygame.Rect(0,0,0,0)
		##	Seems we need to set the width and height before setting the center, shit gets wonky otherwise
		self.bground.width = int(sizes[0] * ref[0])
		self.bground.height = int(sizes[1] * ref[1])
		self.bground.center = (int(coords[0] * ref[0]), int(coords[1] * ref[1]))
		
		if type == 'vertical':
			self.fground = pygame.Rect(0,0,0,0)
			self.fground.width = self.bground.width
			self.fground.height = 10
			self.fground.center = (int(coords[0] * ref[0]), self.bground.bottom)
		
		
		self.rect = self.bground
	
	def draw_me(self):
		pygame.draw.rect(screen, self.colors[0], self.bground)
		pygame.draw.rect(screen, self.colors[1], self.fground)
	
	def update(self, pos):
		print('update fground object', pos)
		if self.type == 'vertical':
			##	still not working as intended.  need to find better way to manage shape heights/positions
			old_y = self.fground.center[1]
			height_diff = pos[1] - self.fground.center[1] + (self.fground.height / 2)
			print(old_y, height_diff)
			self.fground.inflate_ip(0, height_diff)
			self.fground.move_ip(0, (height_diff / 2))
		
		print(self.fground.center[1], self.fground.top)
		
def screen_draw_thread(running):
	while True:
		game_instance.draw_screen(screen)
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
	
	parser = argparse.ArgumentParser(description='Pirate Sim')
	parser.add_argument('-s', '--size', type=str, default='640x720', help='size of the game screen')
	parser.add_argument('-f', '--file', type=str, default=None, help='game save file to load')

	args = parser.parse_args()

	global screen, game_instance
	screen_width, screen_height = [int(numeric_string) for numeric_string in args.size.split('x')]
	screen = pygame.display.set_mode((screen_width, screen_height))
	#pygame.time.Clock.tick(60)
	
	cannonball_update = pygame.USEREVENT + 1
	ship_update = pygame.USEREVENT + 2
	
	pygame.time.set_timer(cannonball_update, 50)
	pygame.time.set_timer(ship_update, 400)
	game_instance = PirateGame()
	if args.file:
		game_instance.load_save(args.file)

	running = True
	
	display_thread = threading.Thread(target = screen_draw_thread, args =(lambda : running, ))
	#display_thread = screen_draw_thread()
	display_thread.start()
	try:
		while(running):
			for event in pygame.event.get():
				if event.type == ship_update:
					game_instance.update_ships()
					break
				if event.type == cannonball_update:
					game_instance.update_cannonballs()
					break
				if event.type == KEYDOWN:
					game_instance.process_event(event.key)
					break
				if event.type == MOUSEBUTTONDOWN:
					game_instance.handle_mouse_press(pygame.mouse.get_pos())
			running = game_instance.get_state()
	except:
		traceback.print_exc(file=sys.stdout)
		running = False
	finally:
		display_thread.join()		
	
if __name__ == "__main__":
	main()



##	have ship rotation and cannon fire working
##	need movement(either simplified or tied to the wind)
##	need to generate random fish spots and a port
##	need to create second ship and start AI
##	need to set target and move ship and execute command on certain conditions

##	thoughts on ui
##	have array of ui elements, loop through all and draw them on screen
##	each needs coords(percentages?), styling, and a function or value to change
##	on mouse click, check if its within the coords of each ui element(pygame.Rect.collidepoint), and execute the function