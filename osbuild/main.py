# Copyright 2013 Daniel Narvaez
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
import pkgutil
import imp

from osbuild import config
from osbuild import environ
from osbuild import plugins
from osbuild import system
from osbuild import build
from osbuild import state
from osbuild import clean
from osbuild import shell


def run_build(clean_all=False):
    if clean_all or state.full_build_is_required():
        clean.clean(build_only=True, new_files=clean_all)
        environ.setup_gconf()

    state.full_build_touch()

    if not build.pull(lazy=True):
        return False

    if not build.build(full=False):
        return False

    return True


def load_plugins():
    for loader, name, ispkg in pkgutil.iter_modules(plugins.__path__):
        f, filename, desc = imp.find_module(name, plugins.__path__)
        imp.load_module(name, f, filename, desc)


def setup(config_args, check_args={}):
    load_plugins()

    config.setup(**config_args)

    if not system.check(**check_args):
        return False

    environ.setup_variables()
    environ.setup_gconf()

    return True


def cmd_clean():
    parser = argparse.ArgumentParser()
    parser.add_argument("module", nargs="?",
                        help="name of the module to clean")
    parser.add_argument("--new-files", action="store_true",
                        help="remove also new files")
    args = parser.parse_args()

    if args.module:
        if not build.clean_one(args.module):
            return False
    else:
        if not clean.clean(new_files=args.new_files):
            return False

    return True


def cmd_pull():
    parser = argparse.ArgumentParser()
    parser.add_argument("module", nargs="?",
                        help="name of the module to pull")
    parser.add_argument("--revisions",
                        help="json dict with the revisions to pull")
    args = parser.parse_args()

    if args.module:
        if not build.pull_one(args.module):
            return False
    else:
        revisions = {}
        if args.revisions:
            revisions = json.loads(args.revisions)

        if not build.pull(revisions):
            return False

    return True


def cmd_shell():
    shell.start()


def cmd_build():
    parser = argparse.ArgumentParser()
    parser.add_argument("module", nargs="?",
                        help="name of the module to build")
    parser.add_argument("--clean-all", action="store_true",
                        help="clean everything before building")
    args = parser.parse_args()

    if args.module:
        if not build.build_one(args.module):
            return False
    else:
        if not run_build(clean_all=args.clean_all):
            return False

    return True
