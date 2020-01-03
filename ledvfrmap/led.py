#!/usr/bin/env python

import logging

RED = (255, 0, 0)
ORANGE = (255, 127, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
INDIGO = (75, 0, 130)
VIOLET = (148, 0, 211)
OFF = (0, 0, 0)

ROYGBIV = [RED, ORANGE, YELLOW, GREEN, BLUE, INDIGO, VIOLET]


def linear_gradient(start_rgb=(0, 0, 0),
                    finish_rgb=(255, 255, 255),
                    n=10):
    gradient = [start_rgb]

    for t in range(1, n):
        curr_rgb = [
            int(start_rgb[j] + (float(t) / (n - 1)) * (finish_rgb[j] - start_rgb[j]))
            for j in range(3)
        ]
        gradient.append(tuple(curr_rgb))

    return gradient


def multi_gradient(points, n=50):
    section_length = int(n / (len(points) - 1))
    gradient = []
    for i in range(len(points) - 1):
        section_count = section_length if i == 0 else section_length + 1
        section = linear_gradient(points[i], points[i + 1], n=section_count)
        if i > 0:
            section = section[1:]
        gradient.extend(section)

    return gradient


class TestLEDController:
    def __init__(self, pixel_count):
        self.pixels = {i: (0, 0, 0) for i in range(pixel_count)}
        self.pixel_state = {i: True for i in range(pixel_count)}
        self.pixel_count = pixel_count

    def stop(self):
        pass

    def all_off(self):
        logger = logging.getLogger(__name__)
        logger.debug("Turning off LEDs")
        for i in range(self.pixel_count):
            self.pixel_state[i] = False

    def all_on(self):
        logger = logging.getLogger(__name__)
        logger.debug("Turning on LEDs")
        for i in range(self.pixel_count):
            self.pixel_state[i] = True

    def is_on(self, pixel_number):
        return self.pixel_state[pixel_number]

    def set_rgb(self, pixel_number, r, g, b):
        logger = logging.getLogger(__name__)
        color = (r, g, b)
        if self.pixels[pixel_number] != color:
            state = "ON" if self.is_on(pixel_number) else "OFF"
            logger.debug("Test controller setting LED ({}) {} to {}".format(state, pixel_number, color))
            self.pixels[pixel_number] = color
 
    def get_rgb(self, pixel_number):
        return self.pixels[pixel_number]
