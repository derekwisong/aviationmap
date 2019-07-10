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
        if self.pixels[pixel_number] != color:
            logger.debug("Test controller setting LED {} to {}".format(pixel_number, color))
            self.pixels[pixel_number] = color
 
    def get_rgb(self, pixel_number):
        return self.pixels[pixel_number]
