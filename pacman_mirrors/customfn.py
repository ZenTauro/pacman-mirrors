#!/usr/bin/env python
#
# This file is part of pacman-mirrors.
#
# pacman-mirrors is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pacman-mirrors is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pacman-mirrors.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors   : Frede Hundewadt <frede@hundewadt.dk>

"""Pacman-Mirrors Custom Functions"""

import os
from .configuration import O_CUST_FILE, CUSTOM_FILE
from .jsonfn import JsonFn
from . import txt


class CustomFn:
    @staticmethod
    def convert_to_json():
        """Convert custom mirror file to json"""
        print(".: {} {}".format(txt.INF_CLR, txt.INF_CONVERT_MIRROR_FILE))
        mirrors = []
        with open(O_CUST_FILE, "r") as mirrorfile:
            mirror_country = None
            for line in mirrorfile:
                country = CustomHelper.get_country(line)
                if country:
                    mirror_country = country
                    continue
                mirror_url = CustomHelper.get_url(line)
                if not mirror_url:
                    continue
                mirror_protocol = CustomHelper.get_protocol(mirror_url)
                # add to mirrors
                mirrors.append({
                    "country": mirror_country,
                    "protocols": [mirror_protocol],
                    "url": mirror_url
                })
            # write new file
            JsonFn.write_json_file(mirrors, CUSTOM_FILE)
            CustomHelper.cleanup()


class CustomHelper:
    @staticmethod
    def cleanup():
        os.remove(O_CUST_FILE)

    @staticmethod
    def get_protocol(data):
        """Extract protocol from url"""
        pos = data.find(":")
        return data[:pos]

    @staticmethod
    def get_country(data):
        """Extract mirror country from data"""
        line = data.strip()
        if line.startswith("[") and line.endswith("]"):
            return line[1:-1]
        elif line.startswith("## Country") or line.startswith("## Location"):
            return line[19:]

    @staticmethod
    def get_url(data):
        """Extract mirror url from data"""
        line = data.strip()
        if line.startswith("Server"):
            return line[9:].replace("$branch/$repo/$arch", "")
