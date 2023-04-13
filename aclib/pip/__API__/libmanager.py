from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Literal, List

import re, os

from .distribution import Distribution
from .colorstr import redstr, yellowstr, greenstr

SELF_PKG_NAME = 'aclib.pip'

class SitePackages(object):
    def __init__(self):
        self.packages = {pkg.name: pkg for pkg in Distribution.iter_installed_distribution()}
        self.__reqs = None
        self.__refs = None

    @property
    def requires(self):
        if self.__reqs is None:
            self.__reqs = {pkgname: self.__get_requires(pkgname, set()) for pkgname in self.packages}
        return self.__reqs

    @property
    def referers(self):
        if self.__refs is None:
            self.__refs = {pkgname: self.__get_referers(pkgname    ) for pkgname in self.packages}
        return self.__refs

    def __get_requires(self, targetname: str, checkexcept: set) -> list:
        requires = self.packages[targetname].requires_localenv
        checkexcept.add(targetname)
        checkset = {*requires} & {*self.packages} - checkexcept
        return sorted(set(sum((self.__get_requires(pkgname, checkexcept) for pkgname in checkset), requires)))

    def __get_referers(self, targetname: str):
        referers = []
        for pkgname in self.requires:
            if targetname in self.requires[pkgname]:
                referers.append(pkgname)
        return referers

    def list(self):
        baseinfos = [[pkg.name, pkg.version] for pkg in self.packages.values()]
        maxnamelen = max(*(len(name) for name, _ in baseinfos), 7)
        maxverlen = max(*(len(ver) for _, ver in baseinfos), 7)
        dsiplay_datas = [['Package', 'Version'], ['-' * maxnamelen, '-' * maxverlen]] + baseinfos
        dsiplay_data = '\n'.join(f'{k:{maxnamelen}} {v:{maxverlen}}' for k, v in dsiplay_datas)
        print(f'\n{dsiplay_data}\n')

    def show(self, *names: str):
        print()
        for pkgname in names or self.packages:
            if pkgname not in self.packages:
                print(f"Package(s) not found: {pkgname}")
                continue
            for item, querykey in {
                'Name': 'name',
                'Version': 'version',
                'Summary': 'summary',
                'Home-page': 'home_page',
                'Author': 'author',
                'Author-email': 'author_email',
                'License': 'license',
            }.items():
                info = getattr(self.packages[pkgname], querykey, '') or '······'
                print(f'{item}: {info}')
            print(f'{"Requires"}: {", ".join(self.requires[pkgname]) or "······"}')
            print(f'{"Required-by"}: {", ".join(self.referers[pkgname]) or "······"}')
            print()

    def __pipuninstall(self, *pkgnames: str):
        print(redstr(f'Would uninstall package(s): {[*pkgnames]}'))
        for pkgname in pkgnames:
            os.system(f'pip uninstall -y {pkgname}')
        self.__init__()

    def uninstall(self, *pkgnames: str, options: List[Literal['-d', '-y']] = None):
        options = options or []
        if not pkgnames:
            return print(redstr('ERROR: You must give at least one package to uninstall'))
        for option in filter(lambda op: op not in ['-d', '-y'], options):
            return print(redstr(f'ERROR: not such option {option}'))

        for uninstalling_pkg in pkgnames:

            print('-'*80)

            if uninstalling_pkg == SELF_PKG_NAME:
                print(redstr(f'ERROR: Do not support to uninstall myself({SELF_PKG_NAME}) temporarily'))
                print(redstr('To uninstall aclib.pip, please use pip'))
                continue
            elif uninstalling_pkg not in self.packages:
                print(yellowstr(f'Uninstallation of "{uninstalling_pkg}" skipped as it is not installed'))
                continue
            else: print(redstr(f'Uninstalling {uninstalling_pkg}-{self.packages[uninstalling_pkg].version}'))

            pkg_referers = self.referers[uninstalling_pkg]
            if pkg_referers:
                print(yellowstr(f'    This package is still required by these installed packages: {pkg_referers}'))
            else: print(greenstr('    This package is not required by other installed packages'))

            print(' '*4 + '-'*40)

            uninstalling_deps = []
            uninstallable_reqs = {*self.requires[uninstalling_pkg]}&{*self.packages}-{'pip', 'setuptools', 'aclib.pip'}
            for req in sorted(uninstallable_reqs):
                if all(reqref in [uninstalling_pkg, *uninstallable_reqs] for reqref in self.referers[req]):
                    uninstalling_deps.append(req)

            if not uninstalling_deps:
                print(greenstr('    There is no installed dependency of uninstalling package'))
            elif '-d' in options:
                print(yellowstr('    The following installed dependencies of uninstaling package is not required by other installed package:'))
                print(yellowstr('\n'.join(f'{i + 1:>9}: {reqname}' for i, reqname in enumerate(uninstalling_deps))))
                print(yellowstr('    They will be uninstalled together'))
            else:
                print(yellowstr(f'    These installed dependencies will not be uninstalled: {uninstalling_deps}'))
                uninstalling_deps.clear()

            if '-y' in options:
                self.__pipuninstall(uninstalling_pkg, *uninstalling_deps)
                continue

            if uninstalling_deps:
                inputtip = 'Enter/y/Y (uninstall all); n/N (cancel); number sequence (uninstall all except selected)'
            else: inputtip = 'y/n/Y/N'

            while True:
                response = input(redstr(f'Proceed? ({inputtip})') + ' --> ')
                if response.strip() in ['y', 'Y'] or response == '':
                    self.__pipuninstall(uninstalling_pkg, *uninstalling_deps)
                    break
                if response.strip() in ['n', 'N']:
                    print(f'UnInstallation of "{uninstalling_pkg}" canceled')
                    break
                if uninstalling_deps:
                    try:
                        response = sorted(set(int(arg) for arg in re.split(r'\s+', response.strip())))
                        for n in response:
                            if not 0 < n <= len(uninstalling_deps): raise TypeError()
                    except: pass
                    else:
                        excludeds = [uninstalling_deps.pop(order-1) for order in response[::-1]]
                        for exclude in excludeds:
                            for req in self.requires[exclude]:
                                if req in uninstalling_deps:
                                    uninstalling_deps.remove(req)
                        self.__pipuninstall(uninstalling_pkg, *uninstalling_deps)
                        break
                print(f"Your response ('{response}') was not one of the expected responses: y/n/Y/N/{{number(1~{len(uninstalling_deps)}) seq}}")
