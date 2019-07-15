#!/usr/bin/env python

import logging

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
