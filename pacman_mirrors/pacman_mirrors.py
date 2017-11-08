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
# Authors: Esclapion <esclapion@manjaro.org>
#          philm <philm@manjaro.org>
#          Ramon Buldó <rbuldo@gmail.com>
#          Hugo Posnic <huluti@manjaro.org>
#          Frede Hundewadt <echo ZmhAbWFuamFyby5vcmcK | base64 -d>

"""Pacman-Mirrors Main Module"""

import argparse
import importlib.util
import os
import shutil
import sys
from operator import itemgetter
from random import shuffle

import pacman_mirrors.functions.util
from pacman_mirrors import __version__
from pacman_mirrors.api import apifn
from pacman_mirrors.config import configfn
from pacman_mirrors.config import configuration as conf
from pacman_mirrors.constants import colors as color
from pacman_mirrors.constants import txt
from pacman_mirrors.functions import filefn
from pacman_mirrors.functions import httpfn
from pacman_mirrors.functions import jsonfn
from pacman_mirrors.functions import validfn
from pacman_mirrors.functions import util
from pacman_mirrors.mirrors import mirrorfn
from pacman_mirrors.mirrors.mirror import Mirror
from pacman_mirrors.translation import i18n
from pacman_mirrors.translation.custom_help_formatter \
    import CustomHelpFormatter

try:
    importlib.util.find_spec("gi.repository.Gtk")
except ImportError:
    GTK_AVAILABLE = False
else:
    GTK_AVAILABLE = True
_ = i18n.language.gettext


class PacmanMirrors:
    """Class PacmanMirrors"""

    def __init__(self):
        """Init"""
        self.config = {
            "config_file": conf.CONFIG_FILE  # purpose - testability
        }
        self.custom = False
        self.default = False
        self.fasttrack = None
        self.geoip = False
        self.interactive = False
        self.max_wait_time = 2
        self.mirrors = Mirror()
        self.network = True
        self.no_mirrorlist = False
        self.no_display = False
        self.quiet = False
        self.selected_countries = []  # users selected countries

    def command_line_parse(self):
        """Read the arguments of the command line"""

        args_summary = "[-h] [-f {}] [-i [-d]] [-m {}]\n" \
                       "\t\t[-c {} [{}...]] [--geoip] [-l]\n" \
                       "\t\t[-b {} | -G | -S/-B {}] [-a] [-p {}]\n" \
                       "\t\t[-P {} [{}...]] [-R] [-U {}]\n" \
                       "\t\t[-q] [-t {}] [-v] [-n]".format(txt.NUMBER,
                                                           txt.METHOD,
                                                           txt.COUNTRY,
                                                           txt.COUNTRY,
                                                           txt.BRANCH,
                                                           txt.BRANCH,
                                                           txt.PREFIX,
                                                           txt.PROTO,
                                                           txt.PROTO,
                                                           txt.URL,
                                                           txt.SECONDS)

        nusage = "\rVersion {}\n{}:\n pacman-mirrors".format(__version__, txt.USAGE)
        usage = "{} {}".format(nusage, args_summary)

        parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter,
                                         add_help=False, usage=usage)

        # Method arguments
        methods = parser.add_argument_group(txt.METHODS)
        methods.add_argument("-f", "-g", "--fasttrack",
                             # action="store",
                             type=int,
                             nargs="*",
                             metavar=txt.NUMBER,
                             help="{}".format(txt.HLP_ARG_FASTTRACK))
        methods.add_argument("-i", "--interactive",
                             action="store_true",
                             help=txt.HLP_ARG_INTERACTIVE)
        methods.add_argument("-d", "--default",
                             action="store_true",
                             help="Interactive: " + txt.HLP_ARG_DEFAULT)
        methods.add_argument("-m", "--method",
                             type=str,
                             choices=["rank", "random"],
                             help=txt.HLP_ARG_METHOD)
        country = parser.add_argument_group(txt.COUNTRY)
        country_geoip = country.add_mutually_exclusive_group()
        country_geoip.add_argument("-c", "--country",
                                   type=str,
                                   nargs="+",
                                   metavar=txt.COUNTRY,
                                   help=txt.HLP_ARG_COUNTRY)
        country_geoip.add_argument("--geoip",
                                   action="store_true",
                                   help=txt.HLP_ARG_GEOIP)
        country.add_argument("-l", "--list", "--country-list",
                             action="store_true",
                             help=txt.HLP_ARG_LIST)
        # Branch arguments
        branch = parser.add_argument_group(txt.BRANCH)
        branch_one = branch.add_mutually_exclusive_group()
        branch_one.add_argument("-b", "--branch",
                                type=str,
                                choices=["stable", "testing", "unstable"],
                                help=txt.HLP_ARG_BRANCH)
        branch_one.add_argument("-G", "--get-branch",
                                action="store_true",
                                help="{}: {}".format(
                                    txt.API, txt.HLP_ARG_API_GET_BRANCH))
        branch_one.add_argument("-S", "-B", "--set-branch",
                                choices=["stable", "testing", "unstable"],
                                help="{}: {}".format(
                                    txt.API, txt.HLP_ARG_API_SET_BRANCH))
        # Api arguments
        api = parser.add_argument_group(txt.API)
        api.add_argument("-a", "--api",
                         action="store_true",
                         help="[-p {}][-R][-S|-G {}][-P {} [{} ...]]".format(
                             txt.PREFIX, txt.BRANCH, txt.PROTO, txt.PROTO))
        api.add_argument("-p", "--prefix",
                         type=str,
                         metavar=txt.PREFIX,
                         help="{}: {} {}".format(
                             txt.API, txt.HLP_ARG_API_PREFIX, txt.PREFIX_TIP))
        api.add_argument("-P", "--proto", "--protocols",
                         choices=["all", "http", "https", "ftp", "ftps"],
                         type=str,
                         nargs="+",
                         help="{}: {}".format(
                             txt.API, txt.HLP_ARG_API_PROTOCOLS))
        api.add_argument("-R", "--re-branch",
                         action="store_true",
                         help="{}: {}".format(
                             txt.API, txt.HLP_ARG_API_RE_BRANCH))
        api.add_argument("-U", "--url",
                         type=str,
                         metavar=txt.URL,
                         help="{}: {}".format(
                             txt.API, txt.HLP_ARG_API_URL))
        # Misc arguments
        misc = parser.add_argument_group(txt.MISC)
        misc.add_argument("-h", "--help",
                          action="store_true")
        misc.add_argument("-q", "--quiet",
                          action="store_true",
                          help=txt.HLP_ARG_QUIET)
        misc.add_argument("-t", "--timeout",
                          type=int,
                          metavar=txt.SECONDS,
                          help=txt.HLP_ARG_TIMEOUT)
        misc.add_argument("-v", "--version",
                          action="store_true",
                          help=txt.HLP_ARG_VERSION)
        sync = misc.add_mutually_exclusive_group()
        sync.add_argument("-n", "--no-mirrorlist",
                          action="store_true",
                          help=txt.HLP_ARG_NO_MIRRORLIST)

        args = parser.parse_args()

        """
        No root required
        """
        if len(sys.argv) == 1 or args.help:
            self.print_help(parser)
            sys.exit(0)

        if args.version:
            print("Version {}".format(__version__))
            sys.exit(0)

        if args.list:
            self.output_country_list()
            sys.exit(0)

        if args.api and args.get_branch:
            self.api_config(get_branch=True)
            sys.exit(0)

        """
        Root required
        """
        if os.getuid() != 0:
            print(".: {} {}".format(
                txt.ERR_CLR, txt.MUST_BE_ROOT))
            sys.exit(1)

        if args.method:
            self.config["method"] = args.method

        if args.branch:
            self.config["branch"] = args.branch

        if args.timeout:
            self.max_wait_time = args.timeout

        if args.quiet:
            self.quiet = True

        """
        Mirrorlist generation
        """
        if args.interactive:
            self.interactive = True
            if not os.environ.get("DISPLAY") or not GTK_AVAILABLE:
                self.no_display = True

        if args.interactive and args.default:
            self.default = True

        # geoip and country are mutually exclusive
        if args.geoip:
            self.geoip = True

        if args.country:
            self.custom = True
            if "," in args.country[0]:
                self.config["only_country"] = args.country[0].split(",")
            else:
                self.config["only_country"] = args.country

            if self.config["only_country"] == ["all"]:
                self.disable_custom_config()

        if args.fasttrack:
            self.fasttrack = args.fasttrack[0]
            if args.fasttrack is None:
                self.fasttrack = 0

        if args.no_mirrorlist:
            self.no_mirrorlist = True

        # api handling
        if args.api:
            getbranch = False
            rebranch = False
            url = args.url
            setbranch = args.set_branch
            setprotocols = bool(args.proto)
            if args.get_branch:
                getbranch = True
            if args.re_branch:
                rebranch = True
            if args.proto:
                if "all" in args.proto:
                    self.config["protocols"] = []
                else:
                    if "," in args.proto:
                        self.config["protocols"] = args.proto.split(",")
                    else:
                        self.config["protocols"] = args.proto

            self.api_config(set_pfx=args.prefix,
                            set_branch=setbranch,
                            re_branch=rebranch,
                            get_branch=getbranch,
                            set_protocols=setprotocols,
                            set_url=url)

    def api_config(self, set_pfx=None, set_branch=None, re_branch=False,
                   get_branch=False, set_protocols=False, set_url=None):
        """Api functions
        :param set_pfx: prefix to the config paths
        :param set_branch: replace branch in pacman-mirrors.conf
        :param re_branch: replace branch in mirrorlist
        :param get_branch: sys.exit with branch
        :param set_protocols: replace protocols in pacman-mirrors.conf
        :param set_url: replace mirror url in mirrorlist
        """
        if set_url is None:
            set_url = ""

        if set_pfx is None:
            set_pfx = ""

        # Order of API tasks does matter
        # First API task
        if get_branch:
            print(self.config["branch"])

        # apply api configuration to internal configuration object
        # Apply prefix if present
        if set_pfx:
            set_pfx = apifn.sanitize_prefix(set_pfx)
            self.config["config_file"] = set_pfx + self.config["config_file"]
            self.config["custom_file"] = set_pfx + self.config["custom_file"]
            self.config["mirror_file"] = set_pfx + self.config["mirror_file"]
            self.config["mirror_list"] = set_pfx + self.config["mirror_list"]
            self.config["status_file"] = set_pfx + self.config["status_file"]
            self.config["work_dir"] = set_pfx + self.config["work_dir"]
            # to be removed long time after 2017-04-18
            self.config["to_be_removed"] = set_pfx + \
                self.config["to_be_removed"]
            # end removal
        # api tasks
        # Second API task: Set branch
        if set_branch:
            # Apply branch to internal config
            self.config["branch"] = set_branch
            # pacman-mirrors.conf could absent so check for it
            if not filefn.check_file(self.config["config_file"]):
                # Copy from host system
                filefn.create_dir(set_pfx + "/etc")
                shutil.copyfile("/etc/pacman-mirrors.conf",
                                self.config["config_file"])
                # Normalize config
                apifn.normalize_config(self.config["config_file"])
            # Write branch to config
            apifn.write_config_branch(self.config["branch"],
                                      self.config["config_file"],
                                      quiet=self.quiet)
        # Third API task: Create a mirror list
        if set_url:
            # mirror list dir could absent so check for it
            filefn.create_dir(set_pfx + "/etc/pacman.d")
            mirror = [
                {
                    "url": apifn.sanitize_url(set_url),
                    "country": "BUILDMIRROR",
                    "protocols": [set_url[:set_url.find(":")]],
                    "resp_time": "00.00"
                }
            ]
            filefn.write_mirror_list(self.config, mirror, quiet=self.quiet)
            sys.exit(0)
        # Fourth API task: Write protocols to config
        if set_protocols:
            apifn.write_protocols(self.config["protocols"],
                                  self.config["config_file"],
                                  quiet=self.quiet)
        # Fifth API task: Rebranch the mirrorlist
        if re_branch:
            if not set_branch:
                print(".: {} {}".format(txt.ERR_CLR, txt.API_ERROR_BRANCH))
                sys.exit(1)
            apifn.write_mirrorlist_branch(self.config["branch"],
                                          self.config["config_file"],
                                          quiet=self.quiet)

    def build_common_mirror_list(self):
        """
        Generate common mirrorlist
        """
        mirror_selection = mirrorfn.filter_mirror_country(self.mirrors.mirrorlist,
                                                          self.selected_countries)
        """
        If we have selected_countries - write a custom-mirror file
        """
        if len(self.selected_countries) < len(self.mirrors.countrylist):
            try:
                _ = self.selected_countries[0]
                self.output_custom_mirror_file(mirror_selection)
            except IndexError:
                pass

        try:
            _ = self.config["protocols"][0]
            mirror_selection = mirrorfn.filter_mirror_protocols(
                mirror_selection, self.config["protocols"])
        except IndexError:
            pass

        """        
        only list mirrors which are up-to-date for users selected branch
        by removing not up-to-date mirrors from the list
        UP-TO-DATE FILTERING NEXT
        """
        mirror_selection = self.filter_user_branch(mirror_selection)

        if self.config["method"] == "rank":
            mirror_selection = self.test_mirrors(mirror_selection)
            mirror_selection = sorted(mirror_selection,
                                      key=itemgetter("resp_time"))
        else:
            shuffle(mirror_selection)

        """
        Try to write mirrorlist
        """
        try:
            _ = mirror_selection[0]
            self.output_mirror_list(mirror_selection)
            if self.custom:
                configfn.modify_config(self.config,
                                       custom=self.custom)
                print(".: {} {} 'sudo {}'".format(txt.INF_CLR,
                                                  txt.REMOVE_CUSTOM_CONFIG,
                                                  txt.RESET_ALL))
            else:
                configfn.modify_config(self.config,
                                       custom=self.custom)
        except IndexError:
            print(".: {} {}".format(txt.WRN_CLR, txt.NO_SELECTION))
            print(".: {} {}".format(txt.INF_CLR, txt.NO_CHANGE))

    def build_fasttrack_mirror_list(self, number):
        """
        Fast-track the mirrorlist by filtering only up-to-date mirrors
        The function takes into account the branch selected by the user
          either on commandline or in pacman-mirrors.conf.
        The function returns  a filtered list consisting of a number of mirrors
        Only mirrors from the active mirror file is used
          either mirrors.json or custom-mirrors.json
        """
        # randomize the load on up-to-date mirrors
        worklist = self.mirrors.mirrorlist
        shuffle(worklist)
        if self.config["protocols"]:
            worklist = mirrorfn.filter_mirror_protocols(
                worklist, self.config["protocols"])

        """
        Only pick mirrors which are up-to-date for users selected branch
          by removin not up-to-date mirrors from the list
        UP-TO-DATE FILTERING NEXT
        """
        up_to_date_mirrors = self.filter_user_branch(worklist)
        worklist = []
        print(".: {}: {} - {}".format(txt.INF_CLR,
                                      txt.QUERY_MIRRORS,
                                      txt.TAKES_TIME))
        counter = 0
        cols, lines = pacman_mirrors.functions.util.terminal_size()
        for mirror in up_to_date_mirrors:
            if not self.quiet:
                message = "   ..... {:<15}: {}: {}".format(
                    mirror["country"], mirror["last_sync"], mirror["url"])
                print("{:.{}}".format(message, cols), end="")
                sys.stdout.flush()
            resp_time = httpfn.get_mirror_response(mirror["url"],
                                                   maxwait=self.max_wait_time,
                                                   quiet=self.quiet)
            mirror["resp_time"] = resp_time
            if float(resp_time) > self.max_wait_time:
                if not self.quiet:
                    print("\r")
            else:
                if not self.quiet:
                    print("\r   {:<5}{}{} ".format(color.GREEN,
                                                   resp_time,
                                                   color.ENDCOLOR))
                worklist.append(mirror)
                counter += 1
            """
            Equality check will stop execution
            when the desired number is reached.
            In the possible event the first mirror's
            responsetime exceeds the predefined responsetime,
            the loop would stop execution if the check for zero is not present
            """
            if counter is not 0 and counter == number:
                break
        worklist = sorted(worklist,
                          key=itemgetter("resp_time"))
        """
        Try to write mirrorlist
        """
        try:
            _ = worklist[0]
            self.output_mirror_list(worklist)
        except IndexError:
            print(".: {} {}".format(txt.WRN_CLR, txt.NO_SELECTION))
            print(".: {} {}".format(txt.INF_CLR, txt.NO_CHANGE))

    def build_interactive_mirror_list(self):
        """
        Prompt the user to select the mirrors with a gui.
        Outputs a "custom" mirror file
        Modify the configuration file to use the "custom" file.
        Outputs a pacman mirrorlist,
        """

        """
        It would seem reasonable to implement a filter
        based on the users branch and the mirrors update status
        On the other hand, the interactive mode is for the user
        to have total control over the mirror file.
        So though it might seem prudent to only include updated mirrors,
        we will not do it when user has selected interactive mode.
        The final mirrorfile will include all mirrors selected by the user
        The final mirrorlist will exclude (if possible) mirrors not up-to-date
        """
        worklist = mirrorfn.filter_mirror_country(self.mirrors.mirrorlist,
                                                  self.selected_countries)
        """
        If config.protols has content, that is a user decision and as such
        it has nothing to do with the reasoning regarding mirrors
        which might or might not be up-to-date
        """
        try:
            _ = self.config["protocols"][0]
            worklist = mirrorfn.filter_mirror_protocols(
                worklist, self.config["protocols"])
        except IndexError:
            pass

        # rank or shuffle the mirrorlist before showing the ui
        if not self.default:
            if self.config["method"] == "rank":
                worklist = self.test_mirrors(worklist)
                worklist = sorted(worklist, key=itemgetter("resp_time"))
            else:
                shuffle(worklist)
        interactive_list = []
        """
        Create a list for display in ui.
        The gui and the console ui expect the supplied list
        to be in the old country dictionary format.
        {
            "country": "country_name",
            "resp_time": "m.sss",
            "last_sync": "HH:MM",
            "url": "http://server/repo/"
        }
        Therefor we have to create a list in the old format,
        thus avoiding rewrite of the ui and related functions.
        We subseqently need to translate the result into:
        a. a mirrorfile in the new json format,
        b. a mirrorlist in pacman format.
        """
        for mirror in worklist:
            # create an entry for all protocols related to a mirror
            for protocol in enumerate(mirror["protocols"]):
                interactive_list.append({
                    "country": mirror["country"],
                    "resp_time": mirror["resp_time"],
                    "last_sync": mirror["last_sync"],
                    "url": "{}{}".format(protocol[1],
                                         util.strip_protocol(mirror["url"]))
                })
        #
        # import the right ui
        if self.no_display:
            # in console mode
            from pacman_mirrors.dialogs import consoleui as ui
        else:
            # gobject introspection is present and accounted for
            from pacman_mirrors.dialogs import graphicalui as ui
        interactive = ui.run(interactive_list,
                             self.config["method"] == "random",
                             self.default)
        # process user choices
        if interactive.is_done:
            mirror_list = []  # to be written to mirrorlist
            mirror_selection = []  # to be written to custom-mirror.json
            custom_list = interactive.custom_list  # grabbing a copy
            # loop custom list
            for custom in custom_list:
                # get url without protocol
                custom_string = util.strip_protocol(custom["url"])
                # locate mirror in the full mirrorlist
                for mirror in self.mirrors.mirrorlist:
                    mirror_string = util.strip_protocol(mirror["url"])
                    # compare urls
                    if custom_string == mirror_string:
                        #
                        # create list for mirror file
                        mirror_selection.append({
                            "country": mirror["country"],
                            "protocols": mirror["protocols"],
                            "url": mirror["url"]
                        })
                        #
                        # create list for mirror list
                        try:
                            # assign user defined protocol if exist
                            _ = self.config["protocols"][0]
                            mirror["protocols"] = self.config["protocols"]
                        except IndexError:
                            pass
                        mirror_list.append(mirror)
            """
            Try selected method on the mirrorlist
            """
            try:
                _ = mirror_list[0]
                if self.default:
                    if self.config["method"] == "rank":
                        mirror_list = self.test_mirrors(mirror_list)
                        mirror_list = sorted(mirror_list,
                                             key=itemgetter("resp_time"))
                    else:
                        shuffle(mirror_list)
            except IndexError:
                pass

            """
            Try to write the mirrorfile and mirrorlist
            """
            try:
                _ = mirror_selection[0]
                self.custom = True
                self.config["only_country"] = ["Custom"]
                self.output_custom_mirror_file(mirror_selection)
                """
                Writing the final mirrorlist
                only write mirrors which are up-to-date for users selected branch
                UP-TO-DATE FILTERING NEXT
                """
                mirror_list = self.filter_user_branch(mirror_list)
                """
                Try writing mirrorlist
                If no up-to-date mirrors exist for users branch
                
                """
                try:
                    _ = mirror_list[0]
                    self.output_mirror_list(mirror_list)
                except IndexError:
                    raise IndexError
            except IndexError:
                print(".: {} {}".format(txt.WRN_CLR, txt.NO_SELECTION))
                print(".: {} {}".format(txt.INF_CLR, txt.NO_CHANGE))

    def disable_custom_config(self):
        """Perform reset of custom configuration"""
        self.config["only_country"] = []
        self.custom = False
        configfn.modify_config(self.config, self.custom)

    def filter_user_branch(self, mirrorlist):
        """Filter mirrorlist on users branch and branch sync state"""
        for idx, branch in enumerate(conf.BRANCHES):
            if branch == self.config["branch"]:
                filtered = []
                for mirror in mirrorlist:
                    if mirror["branches"][idx] == 1:
                        filtered.append(mirror)
                if len(filtered) > 0:
                    return filtered
        return mirrorlist

    def load_all_mirrors(self):
        """
        Load mirrors
        """
        # decision on custom or default
        if self.config["only_country"] == ["Custom"]:
            # check if custom config is valid
            if validfn.custom_config_is_valid():
                self.custom = True
            else:
                self.disable_custom_config()
        else:
            self.selected_countries = self.config["only_country"]
        # decision on custom vs countries from conf or argument
        if self.custom and not self.selected_countries:
            self.load_custom_mirrors()
            self.selected_countries = self.mirrors.countrylist
        else:
            self.load_default_mirrors()
        # validate selection and build country list
        self.selected_countries = mirrorfn.build_country_list(
            self.selected_countries, self.mirrors.countrylist, self.geoip)

    def load_custom_mirrors(self):
        """
        Load available custom mirrors
        """
        if self.default:
            self.load_default_mirrors()
        else:
            self.seed_mirrors(self.config["custom_file"])
            # update custom mirror file with data from status.json
            self.mirrors.mirrorlist = mirrorfn.get_custom_mirror_status(
                self.config, self.mirrors.mirrorlist)

    def load_default_mirrors(self):
        """
        Load all available mirrors
        """
        (file, status) = filefn.return_mirror_filename(self.config)
        self.seed_mirrors(file, status)

    def output_country_list(self):
        """
        List all available countries
        """
        self.config["only_country"] = ["all"]
        self.load_all_mirrors()
        print("{}".format("\n".join(self.mirrors.countrylist)))

    def output_custom_mirror_file(self, selected_mirrors):
        """
        Output selected mirrors to custom mirror file
        :param selected_mirrors:
        :return:
        """
        self.custom = True
        self.config["only_country"] = ["Custom"]
        print("\n.: {} {}".format(txt.INF_CLR,
                                  txt.CUSTOM_MIRROR_LIST))
        print("--------------------------")
        # output mirror file
        jsonfn.write_json_file(selected_mirrors,
                               self.config["custom_file"])
        print(".: {} {}: {}".format(txt.INF_CLR,
                                    txt.CUSTOM_MIRROR_FILE_SAVED,
                                    self.config["custom_file"]))

    def output_mirror_list(self, selected_servers):
        """
        Outputs selected servers to mirrorlist
        :param selected_servers:
        :return:
        """
        if self.custom:
            filefn.write_mirror_list(self.config,
                                     selected_servers,
                                     custom=self.custom,
                                     quiet=self.quiet,
                                     interactive=True)
            configfn.modify_config(self.config,
                                   custom=self.custom)
        else:
            filefn.write_mirror_list(self.config,
                                     selected_servers,
                                     quiet=self.quiet)

    def print_help(self, parser):
        """
        Customized print help
        :param parser:
        :return:
        """
        parser.print_help()
        print("")
        self.print_generate_deprecated()
        self.print_sync_deprecated()
        print("")

    @staticmethod
    def print_generate_deprecated():
        print("{}!! {}: '-g/--generate'!\n"
              "{}   {} '-f/--fasttrack {}'"
              ", {}{}".format(color.RED,
                              txt.DEPRECATED_ARGUMENT,
                              color.BLUE,
                              txt.PLEASE_USE,
                              txt.NUMBER,
                              txt.USE_ZERO_FOR_ALL,
                              color.ENDCOLOR))

    @staticmethod
    def print_sync_deprecated():
        print("{}!! {}: '-y/--sync'!\n"
              "{}   {} 'pacman -Syy'{}".format(color.RED,
                                               txt.DEPRECATED_ARGUMENT,
                                               color.BLUE,
                                               txt.PLEASE_USE,
                                               color.ENDCOLOR))

    def sort_mirror_countries(self):
        self.mirrors.mirrorlist = sorted(self.mirrors.mirrorlist,
                                         key=itemgetter("country"))
        self.mirrors.countrylist = sorted(self.mirrors.countrylist)

    def seed_mirrors(self, file, status=False):
        """Seed mirrors"""
        mirrors = filefn.read_mirror_file(file)
        # seed mirror object
        if status:
            self.mirrors.seed(mirrors, status=status)
        else:
            self.mirrors.seed(mirrors)
        # sort mirrors countrywise
        self.sort_mirror_countries()

    def test_mirrors(self, worklist):
        """Query server for response time"""
        if self.custom:
            print(".: {} {}".format(txt.INF_CLR,
                                    txt.USING_CUSTOM_FILE))
        else:
            print(".: {} {}".format(txt.INF_CLR,
                                    txt.USING_DEFAULT_FILE))
        print(".: {} {} - {}".format(txt.INF_CLR,
                                     txt.QUERY_MIRRORS,
                                     txt.TAKES_TIME))
        cols, lines = pacman_mirrors.functions.util.terminal_size()
        # set connection timemouts
        http_wait = self.max_wait_time
        ssl_wait = self.max_wait_time * 2
        ssl_verify = self.config["ssl_verify"]
        for mirror in worklist:
            colon = mirror["url"].find(":")
            url = mirror["url"][colon:]
            for idx, proto in enumerate(mirror["protocols"]):
                mirror["url"] = "{}{}".format(proto, url)
                if not self.quiet:
                    message = "   ..... {:<15}: {}".format(mirror["country"],
                                                           mirror["url"])
                    print("{:.{}}".format(message, cols), end="")
                    sys.stdout.flush()
                # https sometimes takes longer for handshake
                if proto == "https" or proto == "ftps":
                    self.max_wait_time = ssl_wait
                else:
                    self.max_wait_time = http_wait
                # let's see how responsive you are
                mirror["resp_time"] = httpfn.get_mirror_response(
                    mirror["url"], maxwait=self.max_wait_time,
                    quiet=self.quiet, ssl_verify=ssl_verify)

                if float(mirror["resp_time"]) >= self.max_wait_time:
                    if not self.quiet:
                        print("\r")
                else:
                    if not self.quiet:
                        print("\r   {:<5}{}{} ".format(color.GREEN,
                                                       mirror["resp_time"],
                                                       color.ENDCOLOR))
        return worklist

    def run(self):
        """Run"""
        """
        Build internal config dictionary
        Returns the config dictionary and true/false on custom
        Parse commandline
        Check network
        Break if mirrorlist is not to be touched
        Handle missing network
        """
        (self.config, self.custom) = configfn.build_config()
        filefn.create_dir(self.config["work_dir"])
        self.command_line_parse()
        self.network = httpfn.inet_conn_check()
        if self.network:
            httpfn.update_mirrors(self.config, quiet=self.quiet)
        if self.no_mirrorlist:
            sys.exit(0)
        if not self.network:
            if not self.quiet:
                pacman_mirrors.functions.util.internet_message()
            self.config["method"] = "random"
            self.fasttrack = False
        """
        Load all mirrors
        """
        self.load_all_mirrors()
        """
        Decide which type of mirrorlist to create
        Fasttrack
        Interactive
        Default
        """
        if self.fasttrack:
            self.build_fasttrack_mirror_list(self.fasttrack)
        elif self.interactive:
            self.build_interactive_mirror_list()
        else:
            self.build_common_mirror_list()


if __name__ == "__main__":
    app = PacmanMirrors()
    app.run()
