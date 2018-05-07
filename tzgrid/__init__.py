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
import fcntl
import optparse
import os
import struct
import sys
import termios

import configparser
from colorama import Fore
import dateutil.parser
from dateutil.tz import tzutc, gettz, tzlocal
import pytz
from tzgrid.zones import read_geolocation_data


def get_utc_range(count, options):
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


def format_as_am_pm(d, tz):
    d = d.astimezone(tz)
    return d.strftime('%-I') + d.strftime('%p').rstrip("M").lower()


def format_range_am_pm(tz, width, options, days=False):
    work_hour_12 = [
        "8a", "9a", "10a", "11a", "12p", "1p", "2p", "3p",
        "4p", "5p", "6p"]
    count = int(width / 4)
    arr = list(map(
        lambda x: format_as_am_pm(x, tz), get_utc_range(count, options)))
    format = ""
    for i in range(0, len(arr)):
        if i == int(len(arr) / 2):
            format += Fore.RED + "[%3s]" + Fore.RESET + " "
        elif arr[i] == "12a":
            format += Fore.CYAN + "%3s" + Fore.RESET + " "
        elif arr[i] in work_hour_12:
            format += Fore.GREEN + "%3s" + Fore.RESET + " "
        else:
            format += "%3s "
    return format % tuple(arr)


def format_range_hours(tz, width, options):
    count = int(width / 3)
    arr = get_utc_range(count, options)
    format = ""
    for i in range(0, len(arr)):
        hour = arr[i].astimezone(tz).hour
        if i == int(len(arr) / 2):
            format += Fore.RED + "[%02d]" + Fore.RESET + " "
        elif hour == 0:
            format += Fore.CYAN + "%02d" + Fore.RESET + " "
        elif hour >= 8 and hour <= 18:
            format += Fore.GREEN + "%02d" + Fore.RESET + " "
        else:
            format += "%02d "
        arr[i] = hour
    return format % tuple(arr)


def format_range_hours_minutes(tz, width, options):
    count = int(width / 6)
    arr = get_utc_range(count, options)
    format = ""
    for i in range(0, len(arr)):
        hour = arr[i].astimezone(tz).hour
        if i == int(len(arr) / 2):
            format += Fore.RED + "[%05s]" + Fore.RESET + " "
        elif hour == 0:
            format += Fore.CYAN + "%05s" + Fore.RESET + " "
        elif hour >= 8 and hour <= 18:
            format += Fore.GREEN + "%05s" + Fore.RESET + " "
        else:
            format += "%05s "
        arr[i] = arr[i].astimezone(tz).strftime('%H:%M')
    return format % tuple(arr)


def convert_to_day(d, tz):
    d = d.astimezone(tz)
    if d.hour == 0:
        return d.strftime('%a')
    else:
        return ""


def format_range_hours_days(tz, width, options):
    count = int(width / 3)
    arr = list(map(
        lambda x: convert_to_day(x, tz), get_utc_range(count, options)))
    format = ""
    for i in range(0, len(arr)):
        if i == int(len(arr) / 2):
            format += "%-5s"
        else:
            format += "%-3s"
    return format % tuple(arr)


def label_size(arr):
    size = 0
    for entry in arr:
        if len(entry[0]) > size:
            size = len(entry[0])
    return size


def get_sorted_zones(tzs, options):
    now = options.date
    dates = []
    for label, tz in tzs:
        date = now.astimezone(tz)
        dates.append(tuple([label, tz, date]))

    sorted_zones = []
    for label, zone, date in sorted(dates, key=lambda x: x[2].utcoffset()):
        sorted_zones.append(tuple([label, zone]))

    return sorted_zones


def compare_timezones(a, b):
    return get_tz_name(a) == get_tz_name(b)


def get_tz_name(tz):
    return datetime.utcnow().replace(tzinfo=tz, minute=0).tzname()


def lookup_tz(name):
    if gettz(name):
        return name
    geo_data = read_geolocation_data()
    results = search_geolocation_data(geo_data, name)
    return results[0]['timezone']


def check_zones(args):
    zones = []
    for arg in args:
        zones.append(lookup_tz(arg))
    return zones


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


def get_zone_names_from_config():
    """Read the config and return zone names found."""
    user_data = os.environ.get('SNAP_USER_DATA', "~/config/tzgrid/")
    config = configparser.ConfigParser()
    config.read([
        os.path.expanduser(user_data + "/tzgrid.cfg")])
    return config.get('DEFAULT', 'zones', fallback='')


def get_color_label_format(size, tz):
    """
    Generate a format string (colorized) to print out row labels.

    @param size How large will the label column be?
    @param tz The timezone whos name will be printed as a label.
    """
    fmt = "%-" + "%i" % size + "s"
    if compare_timezones(tz, tzlocal()):
        fmt = Fore.BLUE + fmt
        fmt = fmt + Fore.RESET
    return fmt


def print_grid(zone_names, options):
    """
    Print the tzgrid.

    @param zone_names list of zones to print
    @param options command line options to control printing behavior
    """
    tzs = []
    for name in zone_names:
        tz = gettz(name)
        tzs.append(tuple([name, gettz(name)]))

    size = label_size(tzs)
    tzs = get_sorted_zones(tzs, options)

    if not options.twelve:
        fmt = get_color_label_format(size, tz) + "   %s"
        times = format_range_hours_days(
                tzs[0][1], options.width - size - 5, options)
        print(fmt % ("", times))

    for name, tz in tzs:
        fmt = get_color_label_format(size, tz) + " | %s"
        if (options.twelve):
            times = format_range_am_pm(tz, options.width - size - 5, options)
        else:
            times = format_range_hours(tz, options.width - size - 5, options)

        print(fmt % (name, times))


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
