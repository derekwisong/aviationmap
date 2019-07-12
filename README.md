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
