[![Snap Status](https://build.snapcraft.io/badge/dpb1/tzgrid.svg)](https://build.snapcraft.io/user/dpb1/tzgrid)

# tzgrid

Small command line application to view times by timezone in a grid on
your terminal.

# Installation

Snaps provide an easy mechanism to use this.

    sudo snap install tzgrid    # add --edge to get latest master tip

# Usage

    # Print a pre-configured list, or all UTC zones if unconfigured
    tzgrid

    # Show two timezones, specifically by iana timezone id
    # N.B.: this is the best way to be specific
    tzgrid America/New_York Europe/Paris

    # Show two timezones by using search terms that uniquely qualify
    tzgrid 'Washington D.C.' 'Frankfurt am Main'

    # Search for things
    tzgrid --search 'Delhi' [--verbose]

# Config file

Modify the config file in ~/snap/tzgrid/current/tzgrid.cfg to list the
`zones` you wish to appear when you don't override on the command line.

# TODO

- make/snapcraft target to pull in geolocation database at build
- split out into proper python modules
- tests
- better documentation
- make hh:mm a full option
- switch to hh:ms, if any timezone has a non full-hour offset


Geonames data comes from: http://download.geonames.org/export/dump/ and
is Licensed under CC 3.0 Attribution.
