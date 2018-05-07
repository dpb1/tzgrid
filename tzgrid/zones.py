# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from datetime import datetime, timedelta
import os
import pkg_resources
import sys

import configparser
from dateutil.tz import gettz
import pytz
import unicodecsv as csv


def _read_geolocation_data():
    results = []

    filename = pkg_resources.resource_filename(__package__, "cities15000.txt")
    with open(filename, 'rb') as csvfile:
        cityreader = csv.reader(csvfile, encoding='utf-8', delimiter='\t')
        for row in cityreader:
            results.append({
                'geonameid': row[0],
                'name': row[1],
                'asciiname': row[2],
                'alternatenames': row[3],
                'latitude': row[4],
                'longitude': row[5],
                'feature class': row[6],
                'feature code': row[7],
                'country code': row[8],
                'cc2': row[9],
                'admin1 code': row[10],
                'admin2 code': row[11],
                'admin3 code': row[12],
                'admin4 code': row[13],
                'population': row[14],
                'elevation': row[15],
                'dem': row[16],
                'timezone': row[17],
                'modification date': row[18]})
    return results


def get_utc_range(count, options):
    # TODO: rename
    """
    Generate a range of times in UTC with *now* in the center.

    @param count How large is the rannge to generate?
    @param options command line options
    """
    now = options.date
    arr = [now]
    if count < 3:
        count = 3
    count = count - 1
    half = int(count / 2)
    for i in range(1, half + 1):
        earlier = now - timedelta(hours=i)
        later = now + timedelta(hours=i)
        arr.insert(0, earlier)
        arr.append(later)
    return arr


def get_tz_name(tz):
    return datetime.utcnow().replace(tzinfo=tz, minute=0).tzname()


def get_utc_zone_names():
    """
    Return all UTC offsets 12 hours on either side of UTC
    """
    offset = [0]
    zones = []
    for x in range(1, 12):
        offset.insert(0, -x)
        offset.append(+x)
    for x in offset:
        zones.append("UTC%+0i" % x)
    return zones


class Zones(object):
    def __init__(self):
        self.geo_data = _read_geolocation_data()

    def lookup(self, name):
        if gettz(name):
            return name
        results = search_geolocation_data(self.geo_data, name)
        return results[0]['timezone']

    def check(self, args):
        # TODO: rename or consolidate
        zones = []
        for arg in args:
            zones.append(self.lookup(arg))
        return zones

    def compare(self, a, b):
        return self.get_tz_name(a) == self.get_tz_name(b)

    def search_pytz_data(search):
        results = []
        for tz in pytz.all_timezones:
            if search.lower() == tz.lower():
                results.append({
                    'name': tz, 'timezone': tz})
        return results

    def search_geolocation_data_field(data, search, field):
        search = search.lower()
        results = []
        for record in data:
            if search in record[field].lower():
                results.append(record)
        return results

    def search_geolocation_data(data, search, verbose=False):
        results = search_pytz_data(search)
        if len(results) == 1:
            return results

        for field in ['name', 'asciiname', 'alternatenames']:
            results = search_geolocation_data_field(data, search, field)
            if len(results) == 1:
                return results
            if len(results) > 1:
                continue

        print("Location '{}' has {} possible matches.  Specify the timezone\n"
            "directly if possible.  Use '--search STRING' to help narrow\n"
            "down your search string.\n".format(
                search, len(results)))
        for record in results:
            print(" * {}: {}".format(
                record['name'],
                record['timezone']))
            if verbose:
                print("   - Population: {}".format(record['population']))
                print("   - ASCII Name: {}".format(record['asciiname']))
                print("   - Alternate Names: {}".format(record['alternatenames']))
        sys.exit(1)



def get_zone_names_from_config():
    """Read the config and return zone names found."""
    user_data = os.environ.get('SNAP_USER_DATA', "~/config/tzgrid/")
    config = configparser.ConfigParser()
    config.read([
        os.path.expanduser(user_data + "/tzgrid.cfg")])
    return config.get('DEFAULT', 'zones', fallback='')



def get_zone_names(options, args):
    """
    Return the time zone names specified by the user (or defaults), as a list.
    Config, options, arguments are all consulted.

    @param options command line options
    @param args command line arguments
    """
    config = get_zone_names_from_config()
    if len(args) >= 1:
        zone_names = args
    elif options.utc:
        zone_names = get_utc_zone_names()
    elif config:
        zone_names = config.split(",")
    else:
        zone_names = get_utc_zone_names()
    return zone_names



