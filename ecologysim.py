# Imports
from perlin_noise import PerlinNoise
from tkinter import *
from PIL import ImageTk, Image
import random
from math import sqrt
import csv

# Constant
WINDOW_SIZE = 256
GRID_SIZE = 4096

# Borrowed from last year's algorithms class

def quicksort(array, bottom = 0, top = None, depth = 0):
		if top == None:
				top = len(array) - 1
		if bottom >= top or bottom < 0 or all(i == array[top] for i in array[bottom:top]):
				return
		p = _partition(array, bottom, top)
		try:
				quicksort(array, bottom, p - 1, depth + 1)
				quicksort(array, p + 1, top, depth + 1)
		except RecursionError:
				pass

def _partition(array, bottom, top):
		pivot = array[top][1]
		i = bottom - 1
		for j in range(bottom, top):
				if array[j][1] <= pivot:
						i += 1
						array[i], array[j] = array[j], array[i]
		i += 1
		array[i], array[top] = array[top], array[i]
		return i

# Framework Functions

class Object():
	def __init__(this, x, y, radius, color):
		assert x <= GRID_SIZE
		assert y <= GRID_SIZE
		this.x = x
		this.y = y
		this.radius = radius
		this.color = color
		objects.append(this)
	def tick(this):
		pass

def raycast(this, seenobjects):
	newseenobjects = []
	for i in range(0, len(seenobjects)):
		passed = True
		#startaltitude = GridPosToAltitude(this.x, this.y) + 1
		#endaltitude = GridPosToAltitude(seenobjects[i][0].x, seenobjects[i][0].y) + 1 # +1 to account for height
		#altitudevariance = endaltitude - startaltitude
		#for j in range(0, seenobjects[i][1]):
		#	nextpoint = (seenobjects[i][0].x - this.x, seenobjects[i][0].y - this.y)
		#	factor = abs(nextpoint[0]) + abs(nextpoint[1])
		#	if startaltitude + altitudevariance * (j / seenobjects[i][1]) < GridPosToAltitude(nextpoint[0] / factor, nextpoint[1] / factor):
		#		passed = False
		#		break
		if passed:
			newseenobjects.append(seenobjects[i][0])
	return newseenobjects

def GridPosToAltitude(x, y):
	return noise((x / GRID_SIZE * 2, y / GRID_SIZE * 2))

def RenderImage():
	data = []
	PRE_1 = GRID_SIZE // WINDOW_SIZE
	PRE_2 = 1 / GRID_SIZE
	for i in range(WINDOW_SIZE):
		for j in range(WINDOW_SIZE):
			data.append(int((noise(((i * PRE_1 * (visible_terrain / GRID_SIZE) + view_offset_x) * PRE_2, (j * PRE_1 * (visible_terrain / GRID_SIZE) + view_offset_y) * PRE_2)) + 0.5) * 256))
	image = Image.new("L", (WINDOW_SIZE, WINDOW_SIZE))
	image.putdata(data)
	return image

def UpdateImage():
	global tkimage
	tkimage = ImageTk.PhotoImage(RenderImage())
	canvas.itemconfig(canvasimage, image=tkimage)
	DrawObjects()

def RenderObjects():
	rendered = []
	for i in objects:
		if i.x < view_offset_x - i.radius or i.x > view_offset_x + visible_terrain + i.radius:
			continue
		if i.y < view_offset_y - i.radius or i.y > view_offset_y + visible_terrain + i.radius:
			continue
		if i.radius < visible_terrain / WINDOW_SIZE:
			continue
		rendered.append((i, ((i.x - view_offset_x) * (GRID_SIZE // visible_terrain)) * (WINDOW_SIZE / GRID_SIZE), ((i.y - view_offset_y) * (GRID_SIZE // visible_terrain)) * (WINDOW_SIZE / GRID_SIZE)))
	return rendered

def DrawObjects():
	canvas.delete("objects")
	for i in RenderObjects():
		radius = i[0].radius * (WINDOW_SIZE / visible_terrain) * 2
		canvas.create_oval(i[1] - radius, i[2] - radius, i[1] + radius, i[2] + radius, fill=i[0].color, tags="objects")

def GetClickLocationX(event):
	return event.x * (visible_terrain // WINDOW_SIZE) + view_offset_x

def GetClickLocationY(event):
	return event.y * (visible_terrain // WINDOW_SIZE) + view_offset_y

def ZoomIn(event):
	global visible_terrain
	global view_offset_x
	global view_offset_y
	visible_terrain //= 2
	view_offset_x = GetClickLocationX(event)
	view_offset_y = GetClickLocationY(event)
	UpdateImage()

def ResetZoom(event):
	global visible_terrain
	global view_offset_x
	global view_offset_y
	visible_terrain = GRID_SIZE
	view_offset_x = 0
	view_offset_y = 0
	UpdateImage()

def ZoomOut(event):
	global visible_terrain
	if visible_terrain >= GRID_SIZE:
		ResetZoom(event)
		return
	global view_offset_x
	global view_offset_y
	visible_terrain *= 2
	view_offset_x = max(0, min(view_offset_x - (GetClickLocationX(event) - view_offset_x) // 2, GRID_SIZE - visible_terrain))
	view_offset_y = max(0, min(view_offset_y - (GetClickLocationY(event) - view_offset_y) // 2, GRID_SIZE - visible_terrain))
	UpdateImage()

# Ecology Functions

class Sagebrush(Object):
	def __init__(this, x, y):
		super().__init__(x, y, 3, "#7ff097")
		this.remainingGrowth = 240
	def tick(this):
		if this.radius == 2:
			this.remainingGrowth -= 1
			if this.remainingGrowth <= 0:
				this.radius = 3
				this.remainingGrowth = 240

class Animal(Object):
	def __init__(this, x, y, radius, color, speed, visibilitydistance):
		super().__init__(x, y, radius, color)
		this.patience = random.randint(15, 30)
		this.surroundings = []
		this.target = (None, None)
		this.targetobject = None
		this.speed = speed
		this.visibilitydistance = visibilitydistance
		this.look()
	def tick(this):
		this.patience -= 1
		if this.patience <= 0:
			this.patience = 15
			this.look()
		if this.target[0] == None:
			this.findtarget()
		intendedmove = [this.target[0] - this.x, this.target[1] - this.y]
		factor = (abs(intendedmove[0]) + abs(intendedmove[1]))
		if factor == 0:
			factor = 1
		else:
			factor = this.speed / factor
			if factor > 1:
				factor = 1
		this.x += round(intendedmove[0] * factor)
		this.y += round(intendedmove[1] * factor)
		if this.x == this.target[0] and this.y == this.target[1]:
			this.targetReached()
			this.target = (None, None)
		this.foodHandling()
	def look(this):
		seenobjects = []
		for i in objects:
			distance = int(sqrt((this.x - i.x) ** 2 + (this.y - i.y) ** 2))
			if distance < this.visibilitydistance:
				seenobjects.append((i, distance))
		quicksort(seenobjects)
		this.surroundings = raycast(this, seenobjects)
		this.findtarget()
	def findtarget(this):
		pass
	def foodHandling(this):
		pass
	def targetReached(this):
		pass

class Rabbit(Animal):
	def __init__(this, x, y):
		this.food = 60
		this.reproduction = 0
		super().__init__(x, y, 1, "#f2c768", 4, 24)
	def findtarget(this):
		possibletarget = None
		for i in this.surroundings:
			if i.__class__.__name__ == "Bobcat":
				this.target = (this.x - i.x, this.y - i.y)
				break
			if i.__class__.__name__ == "Sagebrush":
				if i.radius == 3 and possibletarget == None and this.food <= 180:
					possibletarget = i
			elif i.__class__.__name__ == "Rabbit":
				if i.food > 180 and this.food > 180 and this.reproduction <= 0:
					i.food -= 60
					this.food -= 120
					this.reproduction = 240
					i.reproducttion = 120
		if possibletarget != None:
			this.target = (possibletarget.x, possibletarget.y)
			this.targetobject = possibletarget
		else:
			this.target = (this.x + random.randint(-16, 16), this.y + random.randint(-16, 16))
		if this.target[0] < 0:
			this.target = (0, this.target[1])
		if this.target[0] > GRID_SIZE:
			this.target = (GRID_SIZE, this.target[1])
		if this.target[1] < 0:
			this.target = (this.target[0], 0)
		if this.target[1] > GRID_SIZE:
			this.target = (this.target[0], GRID_SIZE)
		this.patience -= 4
	def foodHandling(this):
		this.food -= 1
		if this.food <= 0:
			objects.remove(this)
		this.reproduction -= 1
		if this.reproduction == 120:
			den = Den(this.x, this.y)
			this.reproduction -= 1
	def targetReached(this):
		if this.targetobject.__class__.__name__ == "Sagebrush":
			this.targetobject.radius = 2
			this.food += 120

class Den(Object):
	def __init__(this, x, y):
		super().__init__(x, y, 2, "#6b3b07")
		this.growthremaining = 240
	def tick(this):
		this.growthremaining -= 1
		if this.growthremaining <= 0:
			for i in range(0, random.randint(4, 8)):
				newrabbit = Rabbit(this.x, this.y)
			objects.remove(this)

class Bobcat(Animal):
	def __init__(this, x, y):
		this.food = 120
		this.reproduction = 0
		super().__init__(x, y, 2, "#a84614", 6, 24)
	def findtarget(this):
		possibletarget = None
		for i in this.surroundings:
			if i.__class__.__name__ == "Rabbit":
				possibletarget = i
		if possibletarget != None:
			this.target = (possibletarget.x, possibletarget.y)
			this.targetobject = possibletarget
		else:
			this.target = (this.x + random.randint(-16, 16), this.y + random.randint(-16, 16))
		if this.target[0] < 0:
			this.target = (0, this.target[1])
		if this.target[0] > GRID_SIZE:
			this.target = (GRID_SIZE, this.target[1])
		if this.target[1] < 0:
			this.target = (this.target[0], 0)
		if this.target[1] > GRID_SIZE:
			this.target = (this.target[0], GRID_SIZE)
		this.patience -= 4
	def foodHandling(this):
		this.food -= 1
		if this.food <= 0:
			objects.remove(this)
		this.reproduction -= 1
		if this.reproduction == 240:
			bobcat = Bobcat(this.x, this.y)
			this.reproduction -= 1
	def targetReached(this):
		if this.targetobject.__class__.__name__ == "Rabbit":
			objects.remove(this.targetobject)
			this.food += 240

# Noise Creation
noise = PerlinNoise(10)

# Generic Object Setup

objects = []
#test = Object(512, 512, 64, "red")

# Ecology Setup (plants)

for i in range(0, int(input("Sagebrush plants: "))): # Standard: 4096
	nextObject = Sagebrush(random.randint(0, GRID_SIZE), random.randint(0, GRID_SIZE))

# Ecology Setup (animals)

for i in range(0, 1024):
	nextObject = Rabbit(random.randint(0, GRID_SIZE), random.randint(0, GRID_SIZE))
#for i in range(0, 256):
#	nextObject = Bobcat(random.randint(0, GRID_SIZE), random.randint(0, GRID_SIZE))

# Central Clock (yes it deserves its own section)

ticks = 0
def tick():
	global ticks
	ticks += 1
	for i in objects:
		i.tick()
	if head:
		DrawObjects()
	if recorder and ticks % 10 == 0:
		population = {"Rabbit": 0, "Bobcat": 0, "Den": 0}
		for i in objects:
			if i.__class__.__name__ in ("Rabbit", "Bobcat", "Den"):
				population[i.__class__.__name__] += 1
		record.append(population)
		print(ticks // 10, population, sep="\n")
		if ticks > 2400:
			Dump()
	window.after(300 * head, tick)

# Graphics Toggle
head = False
def toggleGraphics():
	global head
	head = not head

# Data Recorder Configuration
recorder = False
targetFile = input("Enter target CSV file: ")
if targetFile != "":
	recorder = True
	record = []
def Dump():
	for i in record:
		print(i.values(),sep=",")
	file = open(targetFile, "w")
	writer = csv.DictWriter(file, ("Rabbit", "Bobcat", "Den"))
	writer.writeheader()
	writer.writerows(record)
	window.destroy()

# Window Configuration
window = Tk()
window.resizable(width = False, height = False)
canvas = Canvas(window, width=WINDOW_SIZE, height=WINDOW_SIZE)
canvas.pack()
canvasimage = canvas.create_image(0, 0, anchor=NW)
canvas.bind("<Button-1>", ZoomIn)
canvas.bind("<Button-2>", ResetZoom)
canvas.bind("<Button-3>", ZoomOut)
canvas.bind("e", Dump)
canvas.bind("r", toggleGraphics)

ResetZoom(None)
window.after(0, tick)
try:
    window.mainloop()
except KeyboardInterrupt:
    Dump()
