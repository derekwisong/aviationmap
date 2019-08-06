Code for a lighted aviation weather map

https://tutorials-raspberrypi.com/how-to-control-a-raspberry-pi-ws2801-rgb-led-strip/

TDS Best Practices
https://www.aviationweather.gov/dataserver/bestpractices

METAR field description
https://www.aviationweather.gov/dataserver/fields?datatype=metar


https://www.faa.gov/air_traffic/flight_info/aeronav/digital_products/dafd/search/results/?cycle=1907&ident=KHPN&volume=&state=&chart=&advanced=1
<table id="resultsTable" class="striped">

Drawing maps
https://matplotlib.org/basemap/users/geography.html

```
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
m = Basemap(width=12000000,height=9000000,projection='lcc', resolution=None,lat_1=45.,lat_2=55,lat_0=50,lon_0=-107.)
m.shadedrelief()
plt.show()
import sqlite3
import pandas as pd
conn = sqlite3.connect('ledvfrmap.db')
df = pd.read_sql_query("select station_id, FIRST(latitude), FIRST(longitude) from metar group by station_id", conn)
df = pd.read_sql_query("select station_id, latitude, longitude from metar group by station_id, having MIN(ROWID)", conn)
df = pd.read_sql_query("select station_id, latitude, longitude from metar group by station_id having MIN(ROWID)", conn)
df
m
m(df['longitude'], df['latitude'])
m(list(df['longitude']), list(df['latitude']))
x, y = m(list(df['longitude']), list(df['latitude']))
m.scatter(x,y,1, marker='o', color='red')
```

# Features

## Button

- Short press
    - Switch to next mode
- Long press (2s)
    - Replay last 12 hours of current mode
        - Ignore button input for duration of replay
        - Fade lights to 0% over 2 seconds
        - Wait 1 second
        - Replay one hour per second
        - Fade lights to 0% over 2 seconds
        - Wait 1 second
        - Return to current mode's display
    - Return to real-time after replay
- Very long press (5s)
    - Turn off lighs
- If lights are off, next press of any duration turns lights back on

## Brighness

- Brightness automatically controlled using surise/sunset times.
- Or if defined in config file, use that schedule

## Modes

1. Flight category (pulse if wind gusts > 15 kts)
2. Wind speed (blink if wind gusts > 15 kts)
3. Temperature
4. Pressure (altimeter setting)
5. 

# Wish List

- Potentiometer
    - Could be used to control brightness
- Photosensor
    - Automatically adjust brighness according to ambient light