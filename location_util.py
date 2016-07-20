import math
from math import radians, cos, sin, asin, sqrt

from geopy.distance import vincenty
from geopy.geocoders import GoogleV3

import config
from converter_util import ConverterUtil


class LocationUtil(ConverterUtil):
    """
    Utility to help with locations
    """
    def __init__(self, location_name):
        self.latitude = None
        self.longitude = None
        self.altitude = None
        self.set_location(location_name)

    @property
    def latitude_float(self):
        return float(self.latitude)

    @property
    def longitude_float(self):
        return float(self.longitude)

    def set_location(self, location_name):
        """Use google to find a location and set it"""
        geolocator = GoogleV3()
        loc = geolocator.geocode(location_name)

        print('[!] Your given location: {}'.format(loc.address.encode('utf-8')))
        self.set_location_coords(loc.latitude, loc.longitude, loc.altitude)

    def set_location_coords(self, lat, lon, alt):
        """Update the tool location"""
        if config.debug:
            print('[!] lat/long/alt: {} {} {}'.format(lat, lon, alt))
        self.latitude = lat
        self.longitude = lon
        self.altitude = alt

    def get_near(self, map_obj):
        """Returns a PokeStop near the a given map object?"""
        ms = []
        for cell in [map_obj]:
            for block in cell.b:
                for obj in block.c:
                    for stop in obj.s:
                        if self.is_near(stop.lat, stop.lon, self.latitude, self.longitude):
                            ms.append((stop.name, stop.lat, stop.lon,
                                       self.distance(stop.lat, stop.lon, self.latitude, self.longitude)))
        return ms

    def get_near_p(self, map_obj):
        """Returns a PokeStop near the player given map object?"""
        ms = []
        for cell in [map_obj]:
            for block in cell.b:
                for obj in block.c:
                    for stop in obj.p:
                        if self.is_near(stop.lat, stop.lon, self.latitude, self.longitude):
                            ms.append((stop.t.type, stop.lat, stop.lon, stop.name, stop.hash,
                                       self.distance(stop.lat, stop.lon, self.latitude, self.longitude)))
        return ms

    def is_near(self, lat1, lon1, lat2, lon2):
        """Returns whether the distance between two points is smaller than the config distance"""
        return self.distance(lat1, lon1, lat2, lon2) < config.distance

    def distance(self, lat1, lon1, lat2, lon2):
        """Returns distance between two points in meters"""
        lat1 = self.l2f(lat1)
        lon1 = self.l2f(lon1)
        lat2 = self.l2f(lat2)
        lon2 = self.l2f(lon2)
        radius = 6371  # km *1000 m
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) \
            * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = radius * c * 1000
        return d

    def haversine(self, lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points on the earth (specified in decimal degrees)
        """
        lat1 = self.l2f(lat1)
        lon1 = self.l2f(lon1)
        lat2 = self.l2f(lat2)
        lon2 = self.l2f(lon2)

        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers. Use 3956 for miles
        return c * r * 1000

    def is_near_2(self, locx, locy, myx, myy):
        """Returns whether the distance between two points is smaller than the config distance"""
        tmp1 = (self.l2f(locx), self.l2f(locy))
        tmp2 = (self.l2f(myx), self.l2f(myy))
        res = vincenty(tmp1, tmp2).meters
        return res < config.distance
