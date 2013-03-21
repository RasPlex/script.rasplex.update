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

import urllib
import httplib
import os.path
import re
import tarfile
from sets import Set

import xbmc
import xbmcaddon

__addon__       = xbmcaddon.Addon(id='script.rasplex.update')
__addonname__   = __addon__.getAddonInfo('name')

notificationTime = 4000


def showNotification(msg):
	'''
	display a GUI notification
	'''
	print msg
	xbmc.executebuiltin('Notification(%s,%s,%d)' % (__addonname__, msg, notificationTime))


class UpdateError(Exception):
	pass


class SourceForge(object):
	
	baseUrl = "https://sourceforge.net/projects/rasplex/files"
	
	@staticmethod
	def versions():
		'''
		list all versions available for update
		'''
		raise NotImplementedError
		# url = "http://sourceforge.net/api/file/index/project-id/1284489/path/autoupdate/rss"
	
	@staticmethod	
	def downloadURLForVersion(version):
		'''
		get the URL via version string.
		'''
		return "%s/autoupdate/rasplex/rasplex-RPi.arm-%s.tar.bz2/download" % (SourceForge.baseUrl, version)

	@staticmethod
	def versionForName(name):
		'''
		get the URL via release name.
		Valid values for name are:
			- stable
			- bleeding
		'''
		if not name or name == "":
			raise UpdateError("Invalid version name")

		url = "%s/release/%s" % (SourceForge.baseUrl, name)
		r = urllib.urlopen(url)
		if r.getcode() != 200:
			raise UpdateError("Unable to get version from name: Document not found.")
		imgUrl = r.read()
		m = re.search('-(\d+\.\d+\.\d+)\.img', imgUrl)
		if m == None:
			raise UpdateError("Unable to get version from name: Version info not found.")
		return m.group(1)


class Updater(object):
		
	install_dir = "/storage/.update"
		
	@staticmethod
	def _download(url):
		
		r = urllib.urlopen(url)
		if r.getcode() != 200:
			raise UpdateError("Unable to download archive")
		
		percentDone = Set([0])
		def __reportProgress(blocks, blocksize, size):
			percent = (blocksize*blocks*100/size)
			if percent % 5 == 0 and percent not in percentDone:
				percentDone.add(percent)
				showNotification("Download status: %d%%" % percent)

		showNotification("Starting download")		
		archive,m = urllib.urlretrieve(url, reporthook=__reportProgress)
		if os.path.isfile(archive):
			return archive
		else:
			return None

	@staticmethod
	def _extract(archive):
		def target_files(members):
			for tarinfo in members:
				if os.path.dirname(tarinfo.name).endswith("/target"):
					# remove dirname from name 
					tarinfo.name = os.path.basename(tarinfo.name)
					yield tarinfo

		showNotification("Extracting and installing files")		
		try:
			tar = tarfile.open(archive)
			tar.extractall(path=Updater.install_dir, members=target_files(tar))
			tar.close()
		except tarfile.TarError, e:
			raise UpdateError("Extracting archive failed: %s" % e)


	@staticmethod
	def update(url):
		'''
		Update to version given by url.
		Rasies UpdateError on error
		'''
		archive = Updater._download(url)
		print archive
		if not archive:
			raise UpdateError("Download failed")
		
		# create install_dir if not present
		if not os.path.isdir(Updater.install_dir):
			os.mkdir(Updater.install_dir)

		Updater._extract(archive)


if (__name__ == "__main__"):
	import xbmcgui

	xbmcgui.Dialog().ok(__addonname__, "Update started", "This may take some time...")

	versionSetting = __addon__.getSetting('VERSION')
	curr_version=""
	with open ("/etc/version", "r") as versionfile:
		curr_version=versionfile.read().strip()
	
	try:
		version = SourceForge.versionForName(versionSetting)
		
		# check if update is required
		if curr_version == version:
			xbmcgui.Dialog().ok(__addonname__, "Already at version %s" % version)
		
		else:
			showNotification("Updating to version %s" % version)
	
			url = SourceForge.downloadURLForVersion(version)
		
			Updater.update(url)
			showNotification("Update prepared sucessfully. Please reboot to install.")
			ret = xbmcgui.Dialog().yesno(__addonname__, "Update prepared sucessfully", "A reboot is required to finish the installation.", "Reboot now?")
			if ret:
				xbmc.executebuiltin('Reboot')
		
	except UpdateError, e:	
		showNotification("Update failed: %s" % e)
