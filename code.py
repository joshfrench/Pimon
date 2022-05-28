import board
import digitalio
import neopixel
import random
import time

from adafruit_debouncer import Debouncer

class Color(object):
    Red = (255, 0, 0)
    Grn = (0, 255, 0)
    Blu = (0, 0, 255)
    Ylw = (255, 255, 0)
    Off = (0, 0, 0)

class State(object):
    Start = 0
    Display = 1
    Input = 2
    Lose = 3
    Quit = 4

def pinReader(pin: board.Pin):
    io = digitalio.DigitalInOut(pin)
    io.direction = digitalio.Direction.INPUT
    io.pull = digitalio.Pull.UP
    return lambda: io.value

btn0 = Debouncer(pinReader(board.D8))
btn1 = Debouncer(pinReader(board.D5))
btn2 = Debouncer(pinReader(board.D7))
btn3 = Debouncer(pinReader(board.D3))

Buttons = [btn3, btn2, btn1, btn0]

class Pixels(object):
    def __init__(self):
        self.onboard = neopixel.NeoPixel(board.NEOPIXEL, 1)
        self.neopixels = neopixel.NeoPixel(board.D6, 3)
    
    def fill(self, color: tuple[int, int, int]):
        self.onboard.fill(color)
        self.neopixels.fill([x*0.32 for x in color])

    def __getitem__(self, key: int):
        if key == 0:
            return self.onboard[0]
        else:
            return self.neopixels[key - 1]
    
    def __setitem__(self, key: int, value):
        if key == 0:
            self.onboard[0] = value
        else:
            self.neopixels[key - 1] = value

    def __len__(self):
        return 4

    def colorFor(self, px: int):
        return [
            Color.Grn,
            Color.Blu,
            Color.Ylw,
            Color.Red,
        ][px]

    def lum(self, pxl: int, hex: float):
        scale = hex/255.0
        if pxl > 0:
            scale *= 0.32
        self[pxl] = [x*scale for x in self.colorFor(pxl)]

    def bright(self, pxl: int):
        self.lum(pxl, 255)

    def dim(self, pxl: int):
        self.lum(pxl, 64)

pixels = Pixels()

class Game(object):
    def __init__(self):
        self.start()

    def start(self):
        self.state = State.Start
        self.turns = 0
        self.speed = 1.0
        self.presses = []
        self.pattern = [random.randint(0,len(pixels)-1)]
        self.active = time.time()

    def nextTurn(self):
        self.turns += 1
        if self.turns <= 5:
            self.speed -= 0.08
        elif self.turns <= 10:
            self.speed -= 0.06
        elif self.speed > 0.12:
            self.speed -= 0.04
        self.pattern.append(random.randint(0,len(pixels)-1))
        self.presses = []
        print("{{turn: {0}, speed: {1}}}".format(self.turns, self.speed))
        self.state = State.Display

    def guess(self, p: int):
        self.presses.append(p)
        self.active = time.time()
        print(self.presses)
        if len(self.presses) > len(self.pattern):
            self.state = State.Lose
            return
        for i in range(len(self.presses)):
            if self.presses[i] != self.pattern[i]:
                self.state = State.Lose

    def tick(self):
        if time.time() > self.active + 60 and self.state < State.Lose:
            self.state = State.Lose

game = Game()

while True:
    game.tick()

    if game.state == State.Start:
       pixels.fill(Color.Grn)
       time.sleep(0.85)
       pixels.fill(Color.Off)
       time.sleep(0.025)
       game.state = State.Display
    elif game.state == State.Display:
        print(game.pattern)
        for pxl in range(len(pixels)):
            pixels.dim(pxl)
        for pxl in game.pattern:
            time.sleep(game.speed)
            pixels.bright(pxl)
            time.sleep(game.speed)
            pixels.dim(pxl)
        game.state = State.Input
    elif game.state == State.Input:
        for key in Buttons:
            i = Buttons.index(key)
            key.update()
            if key.rose:
                pixels.dim(i)
                if len(game.presses) == len(game.pattern):
                    game.nextTurn()
            if key.fell:
                print("pressed: ", i)
                pixels.bright(i)
                game.guess(i)
    elif game.state == State.Lose:
        blink = 0.13
        speed = 0.07
        for _ in range(3):
            pixels.fill(Color.Red)
            time.sleep(blink)
            pixels.fill(Color.Off)
            time.sleep(speed)
        pixels.fill(Color.Red)
        time.sleep(blink * 2)
        pixels.fill(Color.Off)
        game.state = State.Quit
    elif game.state == State.Quit:
        for key in Buttons:
            key.update()
            if key.fell:
                time.sleep(0.35)
                game.start()
    else:
        pixels.fill(Color.Off)