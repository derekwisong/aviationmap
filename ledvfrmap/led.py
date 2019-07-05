#!/usr/bin/env python

import logging

class TestLEDController:
    def __init__(self, pixel_count):
        self.pixels = {i: (0, 0, 0) for i in range(pixel_count)}
        self.pixel_count = pixel_count

    def stop(self):
        pass

    def all_off(self):
        for i in range(self.pixel_count):
            self.set_rgb(i, 0, 0, 0) 
    
    def set_rgb(self, pixel_number, r, g, b):
        logger = logging.getLogger(__name__)
        color = (r, g, b)
        logger.info("Test controller setting LED {} to {}".format(pixel_number, color))
        self.pixels[pixel_number] = color
 
    def get_rgb(self, pixel_number):
        return self.pixels[pixel_number]

class StationLed:
    def __init__(self, number, controller):
        self.number = number
        self.color = (0, 0, 0)
        self.controller = controller

    def apply_color(self):
        """
        Apply the color value to the LED, if the color has changed
        """
        logger = logging.getLogger(__name__)
        if self.color is None:
            # turn off the led
            logger.info("Turned off LED {}".format(self.number))
            self.controller.set_rgb(self.number, 0, 0, 0)
        else:
            # Set the LED color
            self.controller.set_rgb(self.number, *self.color)
            logger.info("Set LED {} color to {}".format(self.number, self.color))

    def set_rgb(self, r, g, b):
        new_color = (r, g, b)

        if new_color != self.color:
            self.color = new_color
            self.apply_color()

    def turn_off(self):
        self.set_rgb(0, 0, 0)
