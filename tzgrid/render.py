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

from colorama import Fore
from dateutil.tz import gettz, tzlocal


def compare_timezones(a, b):
    return get_tz_name(a) == get_tz_name(b)


def get_tz_name(tz):
    return datetime.utcnow().replace(tzinfo=tz, minute=0).tzname()


def label_size(arr):
    size = 0
    for entry in arr:
        if len(entry[0]) > size:
            size = len(entry[0])
    return size


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
