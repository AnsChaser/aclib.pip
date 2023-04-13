from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self, Iterator

import os, sys, re, platform

def get_environment_variables() -> dict[str, str]:
    def format_full_version(info) -> str:
        version = "{0.major}.{0.minor}.{0.micro}".format(info)
        kind = info.releaselevel
        if kind != "final":
            version += kind[0] + str(info.serial)
        return version
    return {
        "implementation_name": sys.implementation.name,
        "implementation_version": format_full_version(sys.implementation.version),
        "os_name": os.name,
        "platform_machine": platform.machine(),
        "platform_release": platform.release(),
        "platform_system": platform.system(),
        "platform_version": platform.version(),
        "python_full_version": platform.python_version(),
        "platform_python_implementation": platform.python_implementation(),
        "python_version": ".".join(platform.python_version_tuple()[:2]),
        "sys_platform": sys.platform,
    }

class Distribution(object):

    @classmethod
    def iter_installed_distribution(cls, name='') -> Iterator[Self]:
        libpath = os.path.sep.join([*sys.executable.split(os.path.sep)[:-2], 'Lib', 'site-packages'])
        dirprefix = name and re.escape(name + '-') or r'[a-zA-Z0-9]'
        for direntry in os.scandir(libpath):
            if not direntry.is_dir():
                continue
            if not re.search(rf'^{dirprefix}.+?(.dist-info|.egg-info)$', direntry.name):
                continue
            distribution = cls.__new(direntry.path)
            if not name or distribution.name == name:
                yield distribution

    def __new__(cls, distribution_name: str) -> Self | None:
        for dist in cls.iter_installed_distribution(distribution_name):
            return dist
        return None

    @classmethod
    def __new(cls, dist_info_dirpath: str) -> Self:
        self = super().__new__(cls)
        self.__init(dist_info_dirpath)
        return self

    def __init(self, dist_info_dirpath: str):
        self.__homepage = None
        self.__localreqs = None
        self.metadata = {}
        self.requires_dist = {}
        mdata_path, pkginfo_path, req_path = (
            os.path.join(dist_info_dirpath, fname) for fname in ['METADATA', 'PKG-INFO', 'requires.txt'])
        if os.path.isfile(mdata_path):
            self.__loadmetadata(mdata_path)
        if os.path.isfile(pkginfo_path):
            self.__loadmetadata(pkginfo_path)
        if os.path.isfile(req_path):
            self.__loadrequires(req_path)
        for require_dist in self.metadata.get('requires-dist', []):
            require, _, condition = require_dist.partition(';')
            extra_regex = r'(?: and )? *(?<!\S)extra *== *["\'](.*?)["\'] *(?:and )?'
            extra_match = re.search(extra_regex, condition)
            if extra_match:
                extra, marker = extra_match.group(1), re.sub(extra_regex, ' ', condition).strip()
            else: extra, marker = None, condition
            if extra not in self.requires_dist:
                self.requires_dist[extra] = []
            self.requires_dist[extra].append((require, marker))

    def __loadmetadata(self, metadata_path: str):
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadoc = f.read()
        metadoc, _, description = metadoc.partition('\n\n')
        for metak, metav in re.findall(r'^(.+?):(.+)$', metadoc, re.MULTILINE):
            metak, metav = metak.strip().lower(), metav.strip()
            if metak not in self.metadata:
                self.metadata[metak] = []
            self.metadata[metak].append(metav)
        if description:
            self.metadata['description'] = [description]

    def __loadrequires(self, requires_path: str):
        with open(requires_path, 'r', encoding='utf-8') as f:
            requiredoc = f.read()
        for require_group in requiredoc.split('\n\n'):
            require_group_data = require_group.strip().split('\n')
            if require_group_data[0].startswith('['):
                extra, _, marker = require_group_data.pop(0).strip(' []').partition(':')
                extra, marker = extra.strip() or None, marker.strip()
            else: extra, marker = None, ''
            if extra not in self.requires_dist:
                self.requires_dist[extra] = []
            for require in require_group_data:
                self.requires_dist[extra].append((require, marker))

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self.name}-{self.version}>'

    @property
    def name(self):
        return ', '.join(self.metadata.get('name', []))

    @property
    def version(self):
        return ', '.join(self.metadata.get('version', []))

    @property
    def summary(self):
        return ', '.join(self.metadata.get('summary', []))

    @property
    def author(self):
        return ', '.join(self.metadata.get('author', []))

    @property
    def author_email(self):
        return ', '.join(self.metadata.get('author-email', []))

    @property
    def license(self):
        return ', '.join(self.metadata.get('license', []))

    @property
    def home_page(self):
        if self.__homepage is None:
            _homepage = ', '.join(self.metadata.get('home-page', []))
            if not _homepage:
                for _projecturl in self.metadata.get('project-url', []):
                    if re.match(r'homepage *,', _projecturl):
                        _homepage = _projecturl[8:].lstrip(' ,')
                        break
            self.__homepage = _homepage
        return self.__homepage

    @property
    def requires_localenv(self):
        if self.__localreqs is None:
            self.__localreqs = self.filter_requires()
        return self.__localreqs

    def filter_requires(self, *include_extra: str):
        _requires_localenv, include_extra = [], [None, *include_extra]
        for extra, requires in self.requires_dist.items():
            if extra not in include_extra:
                continue
            for require, marker in requires:
                if marker:
                    from pip._vendor.packaging.specifiers import Specifier, InvalidSpecifier
                    env_vars = get_environment_variables()
                for match in re.finditer(r'([^\s(]+?) *( not +in | in |~=|==|!=|===|>|<|>=|<=) *?["\'](.*?)["\']', marker):
                    expression, env_name, comp_op, comp_value = match.group(0, 1, 2, 3)
                    env_value = env_vars[env_name]
                    try:
                        spec = Specifier(comp_op + comp_value)
                        comp_res = spec.contains(env_value)
                    except InvalidSpecifier:
                        comp_res = eval(f'"{env_value}" {comp_op} "{comp_value}"')
                    marker = marker.replace(expression, str(comp_res))
                is_marker_expression_safe = re.sub(r'True|False|and|or|[()]', '', marker).strip() == ''
                if not marker or is_marker_expression_safe and eval(marker):
                    _requires_localenv.append(re.match(r'[\[\], 0-9a-zA-Z._-]+', require).group(0).strip())
        return [*dict.fromkeys(_requires_localenv)]
