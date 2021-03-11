import logging
import signal
import threading
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
        time.sleep(1)

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
    try:
        metars = get_latest_metar([_['code'] for _ in stations])
    except RuntimeError:
        logging.exception("Unable to retrieve metar data")

    # translate METAR into color values
    for station in stations:
        try:
            metar = metars[station['code']]
            color = get_category_color(metar)
        except (NameError, KeyError) as e:
            logging.error(f"Unable to set flight category for {station['name']}")
            color = None

        logger.debug(f"Setting {station['name']} ({station['code']}) to {color}")
        controller.set_led(station['led'], color)

    # tell the LED controller to display the new colors
    controller.show()

class SignalReceiver:
    """
    SignalReceiver is used to trap signals to enable clean shutdown.
    """
    def __init__(self, signals=None):
        """
        Create a SignalReceiver
        signals: Signal numbers to trap. If None, SIGINT and SIGTERM are used
        """
        self._event = threading.Event()

        for signum in signals if signals else [signal.SIGINT, signal.SIGTERM]:
            signal.signal(signum, self._handle)

    @property
    def signaled(self):
        """
        Return true if a signal was received
        """
        return self._event.is_set()
    
    def wait(self, delay):
        """
        Sleep until delay seconds have passed or a signal is received.
        delay: Maximum number of seconds to wait
        Returns true if a signal was received during the wait
        """
        return self._event.wait(delay)

    def _handle(self, signum, frame):
        """
        Handle receiving a signal
        """
        logger.debug(f"Received signal {signum}")
        self._event.set()

def main():
    config = load_config(config_file)
    loglevel = logging.INFO if config['loglevel'] == 'info' else logging.DEBUG
    logging.basicConfig(level=loglevel)

    stations = config['stations']
    leds = [_['led'] for _ in stations]

    # create LED controller which sets and shows LED color values
    try:
        controller = RaspberryPiLedController(leds,
                        config['rpi']['clock_pin'],
                        config['rpi']['data_pin'])
    except NotRaspberryPiException:
        controller = LedController(leds)

    signal_receiver = SignalReceiver()

    while not signal_receiver.signaled:
        update(controller, stations)
        signal_receiver.wait(config['frequency'])
    
    # now that the program is ending, clear the map and wait a second
    controller.clear()
    controller.show()
    time.sleep(1)

if __name__ == '__main__':
    main()