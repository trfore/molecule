#  Copyright (c) 2015 Cisco Systems
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import os
import sys

import yaml
from colorama import Fore

import molecule.utilities as utilities


class Config(object):
    # locations to look for molecule config files
    CONFIG_PATHS = [os.environ.get('MOLECULE_CONFIG'), os.path.expanduser('~/.config/molecule/config.yml'),
                    '/etc/molecule/config.yml']

    def __init__(self):
        """
        Sets up object defaults

        :return: None
        """
        self.molecule = None

    def load_defaults_file(self, defaults_file=None):
        """
        Loads config from a file

        :param defaults_file: optional YAML file to open and read defaults from
        :return: None
        """
        # load defaults from provided file
        if defaults_file is None:
            defaults_file = os.path.join(os.path.dirname(__file__), 'conf/defaults.yml')

        with open(defaults_file, 'r') as stream:
            self.config = yaml.load(stream)

    def merge_molecule_config_files(self, paths=CONFIG_PATHS):
        """
        Looks for a molecule config file in paths and merges it with current config if found

        Only the first file that's found will be merged in.
        :param paths: list of places to look for config files
        :return: Path of file that was merged into config, if found, otherwise None
        """
        # merge defaults with a config file if found
        for path in paths:
            if path and os.path.isfile(path):
                with open(path, 'r') as stream:
                    self.config = utilities.merge_dicts(self.config, yaml.load(stream))
                    return path
        return

    def merge_molecule_file(self, molecule_file=None):
        """
        Looks for a molecule file in the local path and merges it into our config

        :param molecule_file: path and name of molecule file to look for
        :return: None
        """
        if molecule_file is None:
            molecule_file = self.config['molecule_file']

        if not os.path.isfile(molecule_file):
            error = '\n{}Unable to find {}. Exiting.{}'
            print(error.format(Fore.RED, self.config['molecule_file'], Fore.RESET))
            sys.exit(1)

        with open(molecule_file, 'r') as env:
            try:
                self.molecule = yaml.load(env)
            except Exception as e:
                error = "\n{}{} isn't properly formatted: {}{}"
                print(error.format(Fore.RED, self.molecule, e, Fore.RESET))
                sys.exit(1)

            # if molecule file has a molecule section, merge that into our config as
            # an override with the highest precedence
            if 'molecule' in self.molecule:
                self.config = utilities.merge_dicts(self.config, self.molecule['molecule'])

            # merge virtualbox provider options from molecule file with our defaults
            # the format of these data structures is slightly different so we have more logic around it
            for provider in self.molecule['vagrant']['providers']:
                if provider['type'] in self.config['providers']:
                    if 'options' in provider:
                        self.config['providers'][provider['type']]['options'] = utilities.merge_dicts(
                            self.config['providers'][provider['type']]['options'], provider['options'])

    def build_easy_paths(self):
        """
        Convenience function to build up paths from our config values

        :return: None
        """
        self.config['state_file'] = '/'.join([self.config['molecule_dir'], self.config['state_file']])
        self.config['vagrantfile_file'] = '/'.join([self.config['molecule_dir'], self.config['vagrantfile_file']])
        self.config['rakefile_file'] = '/'.join([self.config['molecule_dir'], self.config['rakefile_file']])
        self.config['ansible']['config_file'] = '/'.join([self.config['molecule_dir'], self.config['ansible'][
            'config_file']])
        self.config['ansible']['inventory_file'] = '/'.join([self.config['molecule_dir'], self.config['ansible'][
            'inventory_file']])
