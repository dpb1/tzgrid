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

from datetime import datetime
import fcntl
import optparse
import os
import struct
import sys
import termios

import dateutil.parser
from dateutil.tz import tzutc, tzlocal
import pytz
from tzgrid.zones import (
        read_geolocation_data,
        get_zone_names,
        check_zones,
        search_geolocation_data)
from tzgrid.render import print_grid


def interactive_terminal():
    """Return true only if running in an interactive terminal."""
    if (
            os.isatty(sys.stdin.fileno()) or
            not os.isatty(sys.stdout.fileno())):
        return True
    return False


def terminal_size():
    """Detect and return the terminal size."""
    if not interactive_terminal():
        return 80, 24
    h, w, hp, wp = struct.unpack(
        'HHHH',
        fcntl.ioctl(
            0, termios.TIOCGWINSZ,
            struct.pack('HHHH', 0, 0, 0, 0)))
    return w, h


def setup_parser():
    """Setup the commandline parser."""
    config_parser = optparse.OptionParser()
    config_parser.add_option(
        '-v', '--verbose',
        help='Be more verbose',
        dest="verbose", action="store_true", default=False)
    config_parser.add_option(
        '-s', '--search',
        help='Search the geolocation database directly',
        dest="search", default=None)
    config_parser.add_option(
        '-w', '--width',
        help='Output width, in characters',
        dest="width", default=None)
    config_parser.add_option(
        '-l', '--list',
        help='List all recognized timezones',
        dest="list", action="store_true", default=False)
    config_parser.add_option(
        '-t', '--twelve',
        help='Use 12-hour clock times',
        dest="twelve",
        action="store_true", default=False)
    config_parser.add_option(
        '-d', '--date',
        help='Calculate the grid based on this Date/Time (default=now)',
        dest="date")
    config_parser.add_option(
        '-u', '--utc',
        help='Use list of utc offsets',
        dest="utc", action="store_true", default=False)
    return config_parser


def main():
    (options, args) = setup_parser().parse_args()

    # If terminal width not set, detect
    if options.width is None:
        options.width = int(terminal_size()[0])

    zone_names = get_zone_names(options, args)

    if options.date:
        options.date = dateutil.parser.parse(options.date)
        options.date.replace(tzinfo=tzlocal())
    else:
        options.date = datetime.utcnow().replace(tzinfo=tzutc(), minute=0)

    if options.list:
        for tz in pytz.all_timezones:
            print(tz)
        sys.exit(0)
    if options.search:
        geo_data = read_geolocation_data()
        results = search_geolocation_data(
            geo_data,
            options.search,
            verbose=options.verbose)
        for record in results:
            if record['name'] == record['timezone']:
                print("Exact Match: {}".format(record['timezone']))
            else:
                print("{}: {}".format(
                    record['name'],
                    record['timezone']))
        sys.exit(0)
    else:
        zone_names = check_zones(zone_names)
        print_grid(zone_names, options)


if __name__ == '__main__':
    main()
