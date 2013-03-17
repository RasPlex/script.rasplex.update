import os
import sys
import xbmcaddon

__scriptname__ = "Update RasPlex Settings Dialog"
__author__ = "a_wein"
__version__ = "0.1.0"

__addon__      = xbmcaddon.Addon(id='script.rasplex.update')
__language__   = __addon__.getLocalizedString
__cwd__        = __addon__.getAddonInfo('path')

if __name__ == "__main__":
	__addon__.openSettings()
	
	