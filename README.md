


# Description

## Feature
 - acpip displays packages faster than pip.

 - acpip provides short commands, it make everything so easy.

 - acpip will analyze dependency relationship recursively when uninstall,

   then remind you if uninstalling package is required by other packages or not,

   also list the dependencies which are not required by other packages,
   except pip and setuptools, you can use option -d to uninstall them together.

   although they are not required by other packages, maybe your project is
   using some of them independently. so you can select
   which dependcies not to uninstall before uninstallation start,
   and if you select one, its dependencies will not be uninstalled either.

## About
   This is a new project, i couldn't know all about specification of python distribution temporarily,
   so sometimes i used pip to parse informations, it may be removed in future versions.



# Installation
    pip install aclib.pip



# Usage in command line

## usage
    python -m aclib.pip <command> [options]
    acpip <command> [options]

## commands
    # list installed packages.
    acpip li
    acpip ls
    acpip list


    # show information about all installed packages.
    acpip show

    # show information about given packages.
    acpip show pk1 pkg2 ... pkgn


    # uninstall packages.
    # use option -y to uninstall without comfirm.
    # use option -d to uninstall dependencies together.
    acpip uni [-y/-d] pkg1 pkg2 ... pkgn
    acpip uninstall [-y/-d] pkg1 pkg2 ... pkgn



# Usage in python code

  In addition, this module also provides interfaces to access the informations about installed packages.

    # import aclib.pip
    from aclib.pip import Distribution, SitePackages


