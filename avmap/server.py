"""
$ export FLASK_APP=avmap.server
$ flask run --host=0.0.0.0

curl -w "\n" -X POST http://localhost:5000/station/KHPN/color -H 'Content-Type: application/json' -d '[100, 200, 153]'
curl -w "\n" -X POST http://localhost:5000/show
"""

import time

from typing import Dict, Tuple

from . import config

import Adafruit_WS2801

import flask


CLOCK_PIN = 11
DATA_PIN = 10

Color = Tuple[int, int, int]

class Station:
    code: str = None
    led: int = None
    name: str = None


class StationIndex:
    _by_code: Dict[str, Station] = dict()

    @staticmethod
    def from_config(config: dict) -> "StationIndex":
        index = StationIndex()
        for s in config["stations"]:
            station = Station()
            station.code = s["code"]
            station.name = s["name"]
            station.led = s["led"]

            index._by_code[station.code] = station
        
        return index
    
    def get_station(self, code: str) -> Station:
        return self._by_code[code]

    def count(self) -> int:
        return len(self._by_code)


class LightStrip:
    def __init__(self, length: int):
        assert length >= 0
        self.length = length
        self.strip = Adafruit_WS2801.WS2801Pixels(length, clk=CLOCK_PIN, do=DATA_PIN)
        self.strip.clear()
        self.show()
    
    def set(self, n: int, color: Color) -> None:
        assert 0 <= n < self.length
        self.strip.set_pixel_rgb(n, *color)
    
    def get(self, n: int) -> Color:
        return self.strip.get_pixel_rgb(n)

    def show(self) -> None:
        self.strip.show()


class Map:
    def __init__(self, strip: LightStrip):
        self.strip = strip

    def set_color(self, station: Station, color: Color) -> None:
        self.strip.set(station.led, color)

    def show(self):
        self.strip.show()



app = flask.Flask(__name__)
cfg = config.read_config()
index = StationIndex.from_config(cfg)
strip = LightStrip(index.count())
map = Map(strip)

@app.route('/station/<code>/color', methods=['GET', 'POST'])
def color(code):
    station = index.get_station(code)

    if flask.request.method == 'POST':
        if isinstance(flask.request.json, dict):
            color = flask.request.json["color"]
            show = flask.request.json.get("show", False)
        else:
            color = flask.request.json
            show = False

        map.set_color(station, (color[0], color[1], color[2]))

        if show:
            map.show()

        return "OK", 200
    else:
        color = strip.get(station.led)
        return flask.jsonify(color)

@app.route('/show', methods=['POST'])
def show():
    if flask.request.method == 'POST':
        map.show()
        return "OK", 200
