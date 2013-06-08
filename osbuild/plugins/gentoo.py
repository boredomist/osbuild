import os
import subprocess

from osbuild import command
from osbuild import distro
from osbuild.plugins import interfaces


class PackageManager(interfaces.PackageManager):
    def __init__(self, test=False, interactive=True):
        self._test = test
        self._interactive = interactive

        print("""~~~~~ WARNING ~~~~~

Gentoo support is non-official, and very likely broken beyond repair. Please
report any issues encountered at http://github.com/boredomist/osbuild/issues

You have been warned.""")

    def install_packages(self, packages):
        args = ["emerge", "-vu"]

        if self._interactive:
            args.append("-a")

        args.extend(packages)

        command.run_with_sudo(args, test=self._test)

    def remove_packages(self, packages):
        args = ["emerge", "-vc"]
        args.extend(packages)

        if self._interactive:
            args.append("-a")

        print(args)

        command.run_with_sudo(args, test=self._test)

    def update(self):
        args = ["emerge", "-uvDN"]

        if self._interactive:
            args.append("-a")

        command.run_with_sudo(args, test=self._test)

    # TODO: This currently uses eix, which is non-standard (but common)
    def find_all(self):
        packages = subprocess.check_output(["eix", "-I", "--only-names"])

        return packages.split(" ")

    # TODO
    def find_with_deps(self, packages):
        result = []

        for package in packages:
            if package not in result:
                result.append(package)

            self._find_deps(package, result)

        return result

    def _find_deps(self, package, result):

        # Ensure that package exists first
        try:
            print('_find_deps1')
            subprocess.check_output(["eix", "-IAe", package, "--format",
                                     '<name>'])
        except subprocess.CalledProcessError:
            print("Package %s not installed" % package)
            return
        print('_find_deps')
        # FIXME: This command is horrifying
        f = os.popen("""equery --quiet list emacs |
                        xargs equery --no-color --quiet depgraph -UAMl |
                        perl -pe 's/\[.*?\]\s+(.*?\/.*?)(-[0-9].*)?$/\1/' |
                        tail -n +2""")

        dependencies = f.read().strip().split()
        for dep in dependencies:
            if dep not in result:
                result.append(dep)


distro.register_package_manager("gentoo", PackageManager)


class DistroInfo(interfaces.DistroInfo):
    _GENTOO_RELEASE_PATH = "/etc/gentoo-release"

    def __init__(self):
        arch = self._get_architecture()

        gnome_version = subprocess.check_output(["gnome-about",
                                                 "--gnome-version"])
        gnome_version = gnome_version.split()[1].strip()

        self.name = "gentoo"
        self.version = None
        self.gnome_version = gnome_version
        self.valid = True
        self.supported = (arch in ['i386', 'i686', 'x86_64'])
        self.lib_dir = None

        if arch == "x86_64":
            self.lib_dir = "lib64"

        try:
            with open(self._GENTOO_RELEASE_PATH) as f:
                gentoo_version = f.read().split()[4].strip()
        except IOError:
            gentoo_version = None

        if gentoo_version is None:
            self.valid = False

        if gentoo_version and gentoo_version == '2.2':
            self.version = "2.2"
        else:
            self.supported = False

    def _get_architecture(self):
        return subprocess.check_output(["uname", "-m"]).strip()

distro.register_distro_info(DistroInfo)
