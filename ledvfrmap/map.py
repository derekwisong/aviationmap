#!/usr/bin/env python

import threading
import logging

from . import data

def linear_gradient(start_rgb=(0, 0, 0),
                    finish_rgb=(255, 255, 255),
                    n=10):
    gradient = [start_rgb]

    for t in range(1, n):
      curr_rgb = [
        int(start_rgb[j] + (float(t)/(n - 1)) * (finish_rgb[j] - start_rgb[j]))
        for j in range(3)
       ]
      gradient.append(tuple(curr_rgb))

    return gradient

def multi_gradient(points, n=50):
    section_length = int(n/(len(points) - 1))
    gradient = []
    for i in range(len(points) - 1):
        l = section_length if i == 0 else section_length + 1
        section = linear_gradient(points[i], points[i+1], n=l)
        if i > 0: section = section[1:]
        gradient.extend(section)

    return gradient

def get_led_controller(config):
    if config['controller'] == 'test':
        from .led import TestLEDController
        controller = TestLEDController(config['leds'])   
    else:
        from .rpi import LEDController
        controller = LEDController(config['leds'],
                                   config['rpi']['clock_pin'],
                                   config['rpi']['data_pin'])
        controller.start()

    return controller

class CategoryColorPicker:
    category_colors = {'VFR': (0, 255, 0),
                       'MVFR': (0, 0, 255),
                       'IFR': (255, 0, 0),
                       'LIFR': (255, 0, 255)}
    
    def color(self, value):
        return self.category_colors[value]

    def pick_color(self, station):
        category = station.get_metar_value('flight_category')
        
        try:
            return self.category_colors[category]
        except KeyError:
            return (0, 0, 0)

class GradientColorPicker:
    def __init__(self, min_value, max_value,
                 gradient_start=(0, 0, 255),
                 gradient_end=(255, 0, 0),
                 gradient=None,
                 steps=10,
                 metar='temp_c'):
        self.min_value = min_value
        self.max_value = max_value
        if gradient is not None:
            self.gradient = gradient
            self.steps = len(gradient)
        else:
            self.gradient = linear_gradient(gradient_start, gradient_end, n=steps)
            self.steps = steps
        self.metar = metar

    def color(self, value):
        if value is None: return (0, 0, 0)
        value = min(value, self.max_value)
        value = max(value, self.min_value)
        width = (self.max_value - self.min_value) / (self.steps - 1)
        n = (value - self.min_value) / width
        n = int(round(n))
        return self.gradient[n]

    def pick_color(self, station):
        temperature = station.get_metar_value(self.metar)
        return self.color(temperature)

pickers = {'category': CategoryColorPicker(),
           'temp': GradientColorPicker(-17, 38,
                                       gradient=multi_gradient(((0,0,255),
                                                                (0,255,0),
                                                                (255,0,0)),
                                                               n=14),
                                       metar='temp_c'),
           'wind_speed': GradientColorPicker(0, 20, steps=20, metar='wind_speed_kt'),
           'altimeter': GradientColorPicker(25, 35, steps=10, metar='altim_in_hg')}

class Station(threading.Thread):
    def __init__(self, code, name, led_number, data, led_controller,
            color_picker='category'):
        threading.Thread.__init__(self)
        self.data = data
        self.led_controller = led_controller
        self.led = led_number
        self.set_color_picker(color_picker)
        self._stopped = threading.Event()

        self.code = code
        self.name = name
        self.category = None
        
    def set_color_picker(self, picker_name):
        self.color_picker = pickers[picker_name]

    def set_color(self, r, g, b):
        self.led_controller.set_rgb(self.led, *(r, g, b))
    
    def get_color(self):
        return self.led_controller.get_rgb()
    
    def get_metar_value(self, item):
        return self.data.get_metar_value(self.code, item)

    def run(self):
        logger = logging.getLogger(__name__)
        
        while not self._stopped.wait(1):
            category = self.get_metar_value('flight_category')
            if category != self.category:
                logger.info("{} category changed from {} to {}".format(self.code,
                                                                       self.category,
                                                                       category))
                self.category = category
          
            color = self.color_picker.pick_color(self)
            self.set_color(*color)
    
    def stop(self):
        self._stopped.set()

class LedMap:
    def __init__(self, config):
        logger = logging.getLogger(__name__)
        self.num_leds = config['leds']
        self.data = data.Data(config['database'])
        self.stations = {}
        self.led_controller = get_led_controller(config)
        led_seen = set()

        for station in config['stations']:
            code = station['code']
            name = station['name']
            num = station['led']

            if code is None or num is None:
                continue
            elif num > self.num_leds - 1:
                message = "LED number for {} is out of range".format(code)
                raise Exception(message)

            if code in led_seen:
              raise Exception("LED {} already seen".format(code))
            else:
              led_seen.add(code)

            self.data.add_station(code)
            station = Station(code, name, num, self.data, self.led_controller)
            station.set_color_picker(config['color_picker'])
            station.start()
            self.stations[code] = station
        
        self.data.start()
        self.on = True
        self.button = self.setup_button(config['rpi'])

    def setup_button(self, config):
        from . import rpi
        rpi.setup(mode=config['gpio_mode'])
        button_config = config['button']
        button = rpi.Button(self,
                            button_config['pin'],
                            pull=button_config['pull'],
                            long_press_time=button_config['long_press_time'] / 1000,
                            bouncetime=button_config['bounce_time'])
        return button

    def set_all_stations_color(self, r, g, b):
        for station in self.stations.values():
            station.set_color(r, g, b)

    def set_color_picker(self, picker_name):
        for station in self.stations.values():
            station.set_color_picker(picker_name)

    def lights_off(self):
        if self.on:
            self.led_controller.all_off()
            self.on = False

    def lights_on(self):
        if not self.on:
            self.led_controller.all_on()
            self.on = True

    def toggle_on_off(self):
        if self.on:
            self.lights_off()
        else:
            self.lights_on()
    
    def stop(self):
        self.data.stop()
        self.led_controller.stop()

        for station in self.stations.values():
            station.stop()
