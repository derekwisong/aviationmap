#!/usr/bin/env python

from math import radians, degrees, sin, cos, asin, acos, sqrt

def great_circle(lon1, lat1, lon2, lat2, miles=True):
    factor = 3958.756 if miles else 6371
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    return factor * (
        acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2)))

def haversine(lon1, lat1, lon2, lat2, miles=True):
    factor = 3958.756 if miles else 6371
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * factor * asin(sqrt(a))