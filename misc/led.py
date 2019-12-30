#!/usr/bin/env python

RED = (255, 0, 0)
ORANGE = (255, 127, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
INDIGO = (75, 0, 130)
VIOLET = (148, 0, 211)
        
ROYGBIV = [RED, ORANGE, YELLOW, GREEN, BLUE, INDIGO, VIOLET]


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
