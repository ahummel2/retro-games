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

def positions_diff(pos1, pos2):
	x = math.fabs(pos1[0] - pos2[0])
	y = math.fabs(pos1[1] - pos2[1])
	return math.sqrt(x*x + y*y)

##	max_crew, hull, speed, turning_radius, storage, cannons_per_side
ship_values = [
	[5,10, 3, 3, 300, 10,10, 1, 'sprites/pirate-ship.png'], ##	basic ship with cannons
	[2, 7, 6, 6, 400, 50, 0, 0, 'sprites/pirate-ship.png'], ##	basic fishing ship
]

class PirateGame:
	def __init__(self):
		self.running = False
		self.islands = []
		self.ships = []
		self.cannonballs = []
		self.user_ship = Ship(ship_type=0, state='player')
		self.ships.append(self.user_ship)
		
		
		self.ui_elements = []
		ui_sail = UI_element( (0.94,0.98,0.05,0.95), 'vertical', ((200,150,200), (255,220,100)), self.update_user_ship_sails)
		ui_wheel = UI_element( (0.4,0.6,0.94,0.98), 'horizontal', ((200,150,200), (255,220,100)), self.update_user_ship_wheel)
		self.ui_elements.append(ui_sail)
		self.ui_elements.append(ui_wheel)
		
		self.initiate_world(1200,600)
		self.add_npc_ships()
		self.running = True
	
	def initiate_world(self, x_max, y_max):
		port = Island(0, 0, 10, 0, (random.randrange(x_max), random.randrange(y_max)))
		self.islands.append(port)
		for i in range(5):
			##	should do some checks to make sure random x/y arent overlapping
			atoll = Island(i, 1, 6, 500, (random.randrange(x_max), random.randrange(y_max)))
			self.islands.append(atoll)
		self.wind_angle = random.randrange(360)
		self.wind_speed = random.randrange(6,15)
	
	def add_npc_ships(self):
		sailing_guy = Ship(ship_type=1, state='moving-fish')
		sailing_guy.update_coordinates(500,500)
		##	set this guys target
		random_id = random.randrange(1,6)
		sailing_guy.target = (random_id, self.islands[random_id].pos)
		self.ships.append(sailing_guy)
		
	def objects_to_draw(self):
		objects = self.islands + self.ships + self.cannonballs + self.ui_elements
		return objects
			
	def draw_screen(self, screen):
		screen.fill((130,130,130))
		objects = self.objects_to_draw()
		for each in objects:
			if hasattr(each, 'image'):
				each.image.unlock()
				screen.blit(each.image, each.rect)
			else:
				each.draw_me()
		return True
	
	def load_file(self, path):
		print(path)
	
	def fire_cannons(self, ship, offset):
		x, y = ship.rect.center
		angle = (ship.dir + offset) % 360
		for each in range(ship.cannons_per_side):
			new = Cannonball(angle, ship.cannon_speed, ship.cannon_ticks, (x, y))
			self.cannonballs.append(new)
	
	def process_event(self, event):
		if event == 'EXIT' or event == K_ESCAPE:
			self.running = False
		if event == K_z:
			self.fire_cannons(self.user_ship, 90)
		if event == K_c:
			self.fire_cannons(self.user_ship, -90)
		else:
			pass
		return True
	
	def update_ships(self):
		##	this should process the movements of ships and maybe any cannonballs, or since they've left their ship instance let the game manage those
		#print(self.user_ship.dir, self.user_ship.wheel)
		for ship in self.ships:
			#self.rotate_ship(ship)
			ship.rotate()
			ship.move(self.wind_angle, self.wind_speed)
			if ship.state != 'player':
				ship.update_state()
	
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
				##	if clicked in this rect, call it's update function to handle that, and then if needed whatever method updates the variable elsewhere
				value = each.update(pos)
				each.update_method(value)
	
	def update_user_ship_sails(self, value):
		self.user_ship.sail_setting = value
	
	def update_user_ship_wheel(self, value):
		self.user_ship.wheel = value
	
	def is_running(self):
		return self.running

class Ship:
	def __init__(self, ship_type=0, state=False):
		self.load_ship_stats(ship_type)
		self.ship_type = ship_type
		self.state = state
		self.target = False
		##	Target should ideally hold the target's id and (x, y)
		##	(2, (300,400))
	
	def load_ship_stats(self, type):
		self.max_crew = ship_values[type][0]
		self.hull = ship_values[type][1]
		self.speed = ship_values[type][2]
		self.turning_radius = ship_values[type][3]
		self.inventory = {}
		self.storage_cap = ship_values[type][4]
		self.cannon_speed = ship_values[type][5]
		self.cannon_ticks = ship_values[type][6]
		self.cannons_per_side = ship_values[type][7]
		self.sprite = pygame.image.load(ship_values[type][8]).convert_alpha()
		self.image = self.sprite
		
		self.sail_setting = 0
		self.sail_angle = 0
		self.dir = 0
		self.wheel = 0
		self.rect = self.image.get_rect()
		self.rect.center = (200,200)
		
	def update_coordinates(self, x, y):
		self.rect.center = (x, y)
	
	def rotate(self):
		x, y = self.rect.center
		##	wheel here is -1 to 1, left to right.  reverse of how were calculating angle/direction, so need to subtract the value
		angle = (self.dir - self.wheel * self.turning_radius) % 360
		self.image = pygame.transform.rotate(self.sprite, angle)
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		angle = (self.dir - self.wheel * self.turning_radius) % 360
		self.dir = angle
		
		##	have a separate (or overloaded) method for this that rotates a ship to point at its target
		##	delta_x = self.rect.center[0] - self.target[1][0]
		##	delta_y = self.rect.center[1] - self.target[1][1]
		##	radian_angle = math.atan2(delta_y, delta_x)
	
	def move(self, wind_angle, wind_speed):
		##	calculate the pct of wind the sails are catching(angle of boat/sales vs angle of wind)
		##	think that's abs(sin(angle1 - angle2)) basically
		##	need to convert this to use the sail angle, and I guess remove some abs functions
		angle_diff = math.fabs((wind_angle - self.dir) % 360)
		wind_catch_pct = math.fabs(math.sin(math.radians(angle_diff)))
		wind_force = wind_catch_pct * wind_speed
		speed = wind_force * self.speed * self.sail_setting
		
		##	then move the boat some amount based on its direction and the wind force
		current_x, current_y = self.rect.center
		new_x = int(math.cos(math.radians(self.dir)) * speed)
		new_y = int(math.sin(math.radians(self.dir)) * speed)
		##	subtract the y, because shits inverted here
		self.rect.center = (current_x + new_x, current_y - new_y)
	
	def update_state(self):	
		# moving-fish, moving-port, fishing, port, evading, attacking
		# things that can trigger state changes:
			# arrive at a fishing location -> fishing
			##	if moving-fish and arrived at target, fish
			# arrive at port -> port(sell)
			##	if moving-port and arrived at target, port
			# fishing location expires -> fish, set target
			##	if fishing and target = False, get new target, moving-fish
			# storage is full -> port, set target
			##	if !available_storage, set target to a port, moving-port
			# storage is empty -> fish, set target
			##	if available_storage, set target to fish, moving-fish
			
			##	if fishing, remove stock, add to storage
			##	if port, sell stock, add gold
			
		if self.ship_type == 1:
			if self.state == False:
				##	find a new target
				self.state = 'moving-fish'
			##	check for state updates first, then do the actual things
			if self.state == 'moving-fish' and positions_diff(self.rect.center, self.target[1]) < 20:
				self.state = fishing
			if self.state == 'moving-port' and positions_diff(self.rect.center, self.target[1]) < 20:
				self.state = port
				
			##	need to find a new target for these 3 state changes
			if self.state == 'fishing' and self.target == False:
				self.state = 'moving-fish'
			if self.state == 'fishing':
				if self.available_storage():
					## remove stock, add to storage
					pass
				else:
					self.state = 'moving-port'
			if self.state == 'port':
				if self.available_storage():
					##	sell stock, add gold
					pass
				else:
					self.state = 'moving-fish'
					
		print(self.state, self.target)
	
	def available_storage(self):
		count = 0
		for item in self.inventory:
			count += self.inventory[item]
		if count < self.storage_cap:
			return True
		else:
			return False

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
	def __init__(self, id, type, size, time, pos):
		self.id = id
		self.size = size
		self.time = time
		self.type = type
		self.pos = pos
		self.sprite = pygame.image.load('sprites/fish_school.jpg').convert_alpha()
		self.image = self.sprite
		self.rect = self.image.get_rect()
		self.rect.center = self.pos

class UI_element:
	def __init__(self, pcts, type, colors, update_method):
		##	coords are the rect center, sizes are the horizontal and vertical values
		##	all represented as percentages of screen size
		self.pcts = pcts
		self.type = type
		self.colors = colors
		self.update_method = update_method
		
		ref = screen.get_size()
		
		##	these 4 refer to the background/overall rect, not any overlay
		self.x_left = int(pcts[0] * ref[0])
		self.x_right = int(pcts[1] * ref[0])
		self.y_top = int(pcts[2] * ref[1])
		self.y_bottom = int(pcts[3] * ref[1])
		
		##	left, top, width, height
		self.bground = pygame.Rect(self.x_left, self.y_top, self.x_right - self.x_left, self.y_bottom - self.y_top)
		
		if self.type == 'vertical':
			height = 0
			self.fground = pygame.Rect(self.x_left, self.y_bottom + height, self.x_right - self.x_left, height)
		if self.type == 'horizontal':
			center = int((self.x_right - self.x_left) * 0.5)
			self.fground = pygame.Rect(self.x_left + center - 4, self.y_top, 8, self.y_bottom - self.y_top)
		
		self.rect = self.bground
	
	def draw_me(self):
		pygame.draw.rect(screen, self.colors[0], self.bground)
		pygame.draw.rect(screen, self.colors[1], self.fground)
	
	def update(self, pos):
		if self.type == 'vertical':
			new_height = self.bground.bottom - pos[1]
			self.fground = pygame.Rect(self.x_left, self.y_bottom - new_height, self.x_right - self.x_left, new_height)
			new_value = float(new_height / (self.y_bottom - self.y_top))
		if self.type == 'horizontal':
			new_position = pos[0]
			self.fground = pygame.Rect(new_position - 4, self.y_top, 8, self.y_bottom - self.y_top)
			##	calculates value from 0 to 1 of current position
			new_value = float((pos[0] - self.x_left) / (self.x_right - self.x_left))
			##	convert from 0 -> 1 to -1 -> 1
			new_value = (((new_value - 0) * (1 - -1)) / (1 - 0)) + -1
			
		return new_value
	
	def resize(self):
		print('resizing function called, will implement later')
		##	easy method may be to create the new rects and replace existing ones and redraw
		##	or basically recall the init function, should pull the new sizes with screen.get_sizes and recalculate everything
		
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
	parser.add_argument('-s', '--size', type=str, default='900x800', help='size of the game screen')
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
			running = game_instance.is_running()
	except:
		traceback.print_exc(file=sys.stdout)
		running = False
	finally:
		display_thread.join()		
	
if __name__ == "__main__":
	main()



##	need movement(either simplified or tied to the wind)
##	need to create second ship and start AI
##	need to set target and move ship and execute command on certain conditions

##	thoughts on ui
##	have array of ui elements, loop through all and draw them on screen
##	each needs coords(percentages?), styling, and a function or value to change
##	on mouse click, check if its within the coords of each ui element(pygame.Rect.collidepoint), and execute the function
#######  done, but need to add horizontal and basic click types of ui elements