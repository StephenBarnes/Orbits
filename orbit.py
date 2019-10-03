import pygame as pg
import numpy as np
import sys
import random
import math

#COLOR = (255,255,255)
BGCOLOR = (0,0,0)
FPS = 60
SCREEN_SHAPE = np.asarray((1920, 1080))
POS_SCALING_FACTOR = SCREEN_SHAPE.min() / 5 # how many pixels per unit of position

NUM_PLANETS = 50
GRAVITATIONAL_CONSTANT = .01
TIME_SCALE = 1. / FPS # each step, pos += TIME_SCALE * velocity
MASS = lambda: random.random() * 5
#MASS = lambda: (random.random() - 0.5) * 10 # this gives negative mass to some
INITIAL_VELOCITY = lambda: np.asarray((random.random(), random.random()))
INITIAL_POS = lambda: np.asarray((random.random(), random.random()))
RADIUS = lambda mass: int(3 * abs(mass)**(1./3))
MAX_FORCE_MAGNITUDE = 100
FRICTION_FRAC = 0.3
CONTROL_ACCEL = 10 # magnitude of keyboard-applied acceleration

VERBOSE = False


def euclidean_norm(x):
	return (x**2).sum()**.5

def distance(a, b):
	#TODO try changing this
	return euclidean_norm(a - b)

def gravitational_attraction(dist, m1, m2, direction_unnormalized):
	#TODO try changing this
	if dist == 0:
		return np.asarray((0., 0.))

	# standard gravity
	magnitude = GRAVITATIONAL_CONSTANT * m1 * m2 / float(dist)
	if abs(magnitude) > MAX_FORCE_MAGNITUDE:
		magnitude = MAX_FORCE_MAGNITUDE * (1 if magnitude > 0 else -1)

	# try making it negative at small distances:
	#magnitude = GRAVITATIONAL_CONSTANT * m1 * m2 * math.log(dist*5) / dist

	# try making it undulating
	#magnitude = math.sin(dist * 5) * GRAVITATIONAL_CONSTANT * m1 * m2 / dist

	return direction_unnormalized * magnitude / euclidean_norm(direction_unnormalized)

class Planet:
	def __init__(self, pos = None, velocity = None, mass=None):
		if pos is None:
			pos = INITIAL_POS()
		if velocity is None:
			velocity = INITIAL_VELOCITY()
		if mass is None:
			mass = MASS()
		self.pos = pos
		self.velocity = velocity
		self.mass = mass
		self.radius = RADIUS(mass)
		self.color = (255,0,0) if mass > 0 else (0,0,255)

	def evolve_position(self):
		self.velocity *= (1. - FRICTION_FRAC * TIME_SCALE)
		self.pos += TIME_SCALE * self.velocity

	def accelerate(self, Others):
		total_force = np.asarray((0., 0.))
		for other in Others:
			dist = distance(self.pos, other.pos)
			force = gravitational_attraction(dist, self.mass, other.mass, other.pos - self.pos)
			total_force += force
		self.velocity += TIME_SCALE * total_force / abs(self.mass)
	
	def __repr__(self):
		return "Planet(%s, %s)" % (self.pos, self.velocity)

	def draw(self, surface, origin_at=None, color=None):
		if color is None: color = self.color
		if origin_at is None:
			relative_pos = self.pos
		else:
			relative_pos = self.pos - origin_at
		screen_pos = np.int0(relative_pos * POS_SCALING_FACTOR + SCREEN_SHAPE/2)
		pg.draw.circle(surface, color, screen_pos, self.radius) # (yes, the pos here is the center, not corner)


if True:
	Planets = [Planet() for i in xrange(NUM_PLANETS)]
	# Allocate masses negative and positive in roughly equal proportion
	#for i, p in enumerate(Planets):
	#	if i < NUM_PLANETS/2:
	#		p.mass = abs(p.mass)
	#	else:
	#		p.mass = -abs(p.mass)
	Planets.sort(key = lambda p: p.mass, reverse = True) # so we control the planet with highest (positive) mass

	clock = pg.time.Clock()
	pg.init()
	screen = pg.display.set_mode(SCREEN_SHAPE)

	while True:
		try:
			for event in pg.event.get():
				if event.type == pg.QUIT:
					sys.exit(0)
				elif event.type == pg.KEYDOWN:
					if event.key == pg.K_ESCAPE:
						sys.exit(0)

			if VERBOSE: print "updating planets..."
			for i, planet in enumerate(Planets):
				planet.accelerate(Planets[:i] + Planets[i+1:])
				planet.evolve_position()

			# allow movement of the first planet
			pressed = pg.key.get_pressed()
			if pressed[pg.K_UP]: Planets[0].velocity[1] -= CONTROL_ACCEL * TIME_SCALE
			if pressed[pg.K_DOWN]: Planets[0].velocity[1] += CONTROL_ACCEL * TIME_SCALE
			if pressed[pg.K_LEFT]: Planets[0].velocity[0] -= CONTROL_ACCEL * TIME_SCALE
			if pressed[pg.K_RIGHT]: Planets[0].velocity[0] += CONTROL_ACCEL * TIME_SCALE

			if pressed[pg.K_SPACE]: # freeze velocities
				for planet in Planets:
					planet.velocity = np.asarray((0., 0.))

			if pressed[pg.K_r]: # negative friction, ie heating up
				FRICTION_FRAC = -abs(FRICTION_FRAC)
			if pressed[pg.K_f]: # positive friction
				FRICTION_FRAC = abs(FRICTION_FRAC)

			if pressed[pg.K_a]: # zoom in
				POS_SCALING_FACTOR *= 1 + (2. * TIME_SCALE)
			if pressed[pg.K_z]: # zoom out
				POS_SCALING_FACTOR *= 1 - (2. * TIME_SCALE)

			if pressed[pg.K_t]: # slow down
				TIME_SCALE *= 0.99
			if pressed[pg.K_s]: # speed up
				TIME_SCALE *= 1.01

			screen.fill(BGCOLOR)

			# recompute center of pos, since friction and arithmetic errors can change it
			#center_of_pos = sum(p.pos for p in Planets) / float(NUM_PLANETS)

			if VERBOSE:
				print
				print "drawing planets:"
			for i, planet in enumerate(Planets):
				planet.draw(screen, origin_at = Planets[0].pos, color = ((255,255,255) if i != 0 else None))
				if VERBOSE: print planet

			pg.display.flip()
			clock.tick(FPS)
		except KeyboardInterrupt as e:
			sys.exit(0)

