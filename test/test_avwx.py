import unittest

import avwx.tds

class TestMetar(unittest.TestCase):
    """Tests for METAR data"""
    
    def test_metar_structure_single(self):
        metar = avwx.tds.get_latest_metar("KATL")
        self.assertIsInstance(metar, dict)
        self.assertEqual(metar['station_id'], "KATL")
    
    def test_metar_structure_multiple(self):
        stations = ["KATL", "KJFK"]
        metars = avwx.tds.get_latest_metar(stations)
        self.assertIsInstance(metars, list)
        self.assertEqual(len(metars), len(stations))

        # check that each metar received is for the station provided
        for station, metar in zip(stations, metars):
            self.assertEqual(metar['station_id'], station)
