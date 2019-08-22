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
	
	def draw_screen(self, screen):
		screen.fill((130,130,130))
		objects = self.objects_to_draw()
		for each in objects:
			screen.blit(each.image, each.rect)
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
		print(ship.dir, offset, angle)
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
				
	
	def objects_to_draw(self):
		objects = self.islands + self.ships + self.cannonballs
		return objects
	
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
			running = game_instance.get_state()
	except:
		traceback.print_exc(file=sys.stdout)
		running = False
	finally:
		display_thread.join()		
	
if __name__ == "__main__":
	main()