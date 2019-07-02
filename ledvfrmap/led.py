#!/usr/bin/env python

import logging

class StationLed:
    def __init__(self, number):
        self.number = number
        self.color = (0, 0, 0)

    def apply_color(self):
        """
        Apply the color value to the LED, if the color has changed
        """
        logger = logging.getLogger(__name__)
        if self.color is None:
            # turn off the led
            logger.info("Turned off LED {}".format(self.number))
        else:
            # Set the LED color
            pass
            logger.info("Set LED {} color to {}".format(self.number, self.color))

    def set_rgb(self, r, g, b):
        new_color = (r, g, b)

        if new_color != self.color:
            self.color = new_color
            self.apply_color()

    def turn_off(self):
        self.set_rgb(0, 0, 0)
