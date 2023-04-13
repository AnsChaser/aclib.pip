import sys

from .__API__.colorstr import redstr
from .__API__.libmanager import SitePackages

helpdoc = '\n'.join([
    '',
    'Usage:',
   f'  acpip {"<li/ls/list>":44} List installed packages in local site-packages.',
   f'  acpip {"<show> [pkgs]":44} Show information about given packages, show all when no pkg given.',
   f'  acpip {"<uni/uninstall> [-y/-d/pkgs]":44} Uninstall given packages. No confirm when -y given. Uninstall dependencies also when -d given.',
   f'  acpip {"<help>":44} Show help doc',
   '',
])

def main():
    if len(sys.argv) > 1:
        cmd, args = sys.argv[1], sys.argv[2:]
        if cmd in ['li', 'ls', 'list']:
            return SitePackages().list()
        if cmd == 'show':
            return SitePackages().show(*args)
        if cmd in ['uni', 'uninstall']:
            packages = [arg for arg in args if not arg.startswith('-')]
            options = [arg for arg in args if arg.startswith('-')]
            return SitePackages().uninstall(*packages, options=options)
        if cmd == 'help':
            return print(helpdoc)
        print(redstr(f'ERROR: unknown command "{cmd}"'))
    else: print(helpdoc)

if __name__ == '__main__':
    main()
