import os
import subprocess

from osbuild import command
from osbuild import distro
from osbuild.plugins import interfaces


class PackageManager(interfaces.PackageManager):
    def __init__(self, test=False, interactive=True):
        self._test = test
        self._interactive = interactive

    def install_packages(self, packages):
        args = ["emerge", "-vu"]

        if self._interactive:
            args.append("-a")

        args.extend(packages)

        command.run_with_sudo(args, test=self._test,
                              interactive=self._interactive)

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

        command.run_with_sudo(args, test=self._test,
                              interactive=self._interactive)

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

        self.name = "gentoo"
        self.version = None
        self.gnome_version = "TODO"
        self.gstreamer_version = "TODO"
        self.valid = True

        # TODO: Confirm validity of this
        self.supported = (arch in [b'i386', b'i686', b'x86_64'])

        self.lib_dir = None

        if arch == "x86_64":
            self.lib_dir = "lib64"

        try:
            release = subprocess.check_output(["lsb_release", "-r"])
            release = release.split()[1].strip()
        except:
            release = None
            self.valid = False

        if release == b'2.1':
            self.version = "2.1"
        else:
            self.supported = False

    def _get_architecture(self):
        return subprocess.check_output(["uname", "-m"]).strip()

distro.register_distro_info(DistroInfo)
