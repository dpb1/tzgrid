[![Snap Status](https://build.snapcraft.io/badge/dpb1/tzgrid.svg)](https://build.snapcraft.io/user/dpb1/tzgrid)

# tzgrid

View timezones aligned to a grid in your terminal.

![tzgrid screenshot](tzgrid.png?raw=true "tzgrid screenshot")

# Quick Installation

Snaps provide an easy mechanism to install.

    sudo snap install tzgrid    # add --edge to get latest master tip

See https://snapcraft.io/tzgrid for more details

# Usage

    # Print a pre-configured zone list, or "UTC offset" zones if
    # unconfigured
    tzgrid

    # Show two timezones, specifically by IANA timezone id
    # N.B.: this is the best way to be specific
    tzgrid America/New_York Europe/Paris

    # Show two timezones by using search terms that uniquely qualify
    tzgrid 'Washington D.C.' 'Frankfurt am Main'

    # Search for things
    tzgrid --search 'Delhi' [--verbose]

    # List all available IANA zones
    tzgrid --list

# Features

- Includes database of cities with more than 100,000 people to ease in
  looking up timezones.
- Colored output in the terminal
- Pass in arbitrary time/day or rely on default of 'now'
- DST offsets are calculated correctly
- Workday hours highlighting helps to know when to schedule a meeting.

# Config file

Modify the config file in `~/snap/tzgrid/current/tzgrid.cfg` to list the
`zones` you wish to appear when you don't override on the command line.

# Run from source

    git clone https://github.com/dpb1/tzgrid
    cd tzgrid
    python3 -m venv v
    source v/bin/activate
    pip3 install -r requirements.txt
    python3 -m tzgrid Denver Paris

# TODO

- tests
- make hh:mm a full option
- switch to hh:ms, if any timezone has a non full-hour offset


Geonames data comes from: http://download.geonames.org/export/dump/ and
is licensed under CC 3.0 Attribution.
