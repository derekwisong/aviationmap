import logging
import time
import yaml

from . import config_file
from avwx.tds import get_latest_metar

logger = logging.getLogger(__name__)

flight_category_colors = {
    'VFR': (0, 255, 0),
    'MVFR': (0, 0, 255),
    'IFR': (255, 0, 0),
    'LIFR': (255, 0, 255)}

class LedController:
    """
    Display LED color values to standard output.
    This class acts as a virtual LED strip, useful for testing
    functionality and as a base class for actual LED strips.
    """

    def __init__(self, leds):
        """
        Create an LedController
        leds: List of LEDs
        """

        self.leds = {led: None for led in leds}

    def set_led(self, led, color):
        """
        Set an LED color. The color will not display until
        show() is called.
        led: The LED to update
        color: (r, g, b) tuple
        """
        self.leds[led] = color
    
    def clear(self):
        """
        Clear (turn off) the LEDs. The LEDs will not clear
        until show() is called.
        """
        for led in self.leds.keys():
            self.leds[led] = None

    def show(self):
        """
        Print the LED values to the console
        """
        for led, color in self.leds.items():
            logger.info(f"Setting LED {led} to {color}")

class NotRaspberryPiException(Exception):
    """
    Custom exception to indicate an action which cant be done because
    the device is not a Raspberry Pi
    """
    pass

class RaspberryPiLedController(LedController):
    """
    Display LED color values to a WS2801 strip attached to
    a Raspberry Pi
    """

    def __init__(self, leds, clock_pin, data_pin):
        """
        Create a RaspberryPiLedController.
        leds: List of LED numbers
        clock_pin: GPIO pin that the clock pin on the WS2801 connects to
        data_pin: GPIO pin that the data pin on the WS2801 connects to
        """
        super().__init__(leds)
        import Adafruit_WS2801
        
        try:
            self.pixels = Adafruit_WS2801.WS2801Pixels(len(leds),
                                                       clk=clock_pin,
                                                       do=data_pin)
        except RuntimeError:
            raise NotRaspberryPiException("Unable to load Adafruit_WS2801.")
                                                   

        # clear previously displayed colors from the WS2801
        self.clear()
        self.show()
    
    def clear(self):
        """
        Set all the LEDs to off. The LEDs will not update until show() is called.
        """
        super().clear()
        self.pixels.clear()

    def show(self):
        """
        Update the LED strip to display the currently set colors
        """
        for led, color in self.leds.items():
            if not color:
                color = (0, 0, 0)

            self.pixels.set_pixel_rgb(led, *color)

        self.pixels.show()

def load_config(config_file):
    """Load configuration file"""
    logger.debug(f"Reading configuration from {config_file}")
    with open(config_file, 'rb') as config:
        return yaml.load(config, Loader=yaml.Loader)

def get_category_color(metar):
    """
    Get the color that represents the flight category described by
    the current metar.
    VFR (Visual Flight Rules) - Green
    MVFR (Marginal Visual Flight Rules) - Blue
    IFR (Instrument Flight Rules) - Red
    LIFR (Low Instrument Flight Rules) - Magenta
    """
    
    try:
        return flight_category_colors[metar['flight_category']]
    except KeyError:
        return

def update(controller: LedController, stations):
    """
    Update the LED display to display current data
    controller: The controller to update
    stations: the list of stations that are to be updated
    """

    # get METAR data
    metars = get_latest_metar([_['code'] for _ in stations])

    # translate METAR into color values
    for station in stations:
        metar = metars[station['code']]
        color = get_category_color(metar)
        logger.debug(f"Setting {station['name']} ({station['code']}) to {color}")
        controller.set_led(station['led'], color)
    
    # tell the LED controller to display the new colors
    controller.show()

def main():
    logging.basicConfig(level=logging.INFO)
    config = load_config(config_file)

    stations = config['stations']
    leds = [_['led'] for _ in stations]

    # create LED controller which sets and shows LED color values
    try:
        controller = RaspberryPiLedController(leds,
                        config['rpi']['clock_pin'],
                        config['rpi']['data_pin'])
    except NotRaspberryPiException:
        controller = LedController(leds)

    try:
        while True:
            update(controller, stations)
            time.sleep(config['frequency'])
    except KeyboardInterrupt:
        logging.debug("Interrupt from keyboard")

if __name__ == '__main__':
    main()