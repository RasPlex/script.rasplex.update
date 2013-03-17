# This file is part of the RasPlex Updater add-on for XBMC.
#
# @license   http://www.gnu.org/licenses/gpl.html GPL Version 3
# @author    Andreas Weinlein <andreas.dev@weinlein.info>
# @copyright Copyright (c) 2013 Andreas Weinlein
#
# RasPlex Updater is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# RasPlex Updater is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RasPlex Updater. If not, see <http://www.gnu.org/licenses/>.

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
	
	