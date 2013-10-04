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
import urllib2
import json
import os.path
import re
import tarfile
from sets import Set

import xbmc
import xbmcaddon

__addon__       = xbmcaddon.Addon(id='script.rasplex.update')
__addonname__   = __addon__.getAddonInfo('name')

notificationTime = 4000


def log(msg):
	xbmc.log('RasPlex.Update::' + msg)

def showNotification(msg):
	'''
	display a GUI notification
	'''
	log(msg)
	xbmc.executebuiltin('Notification(%s,%s,%d)' % (__addonname__, msg, notificationTime))

def load_file(filename):
	try:
		if os.path.isfile(filename):
			objFile = open(filename, 'r')
			content = objFile.read()
			objFile.close()
		else:
			content = ""

		return content.strip()

	except Exception, e:	
		log('load_file(' + filename + ')', 'ERROR: (' + repr(e) + ')')


class UpdateError(Exception):
	pass


class System(object):

	SYSTEMID      = load_file('/etc/machine-id')
	DISTRIBUTION  = load_file('/etc/distribution')
	ARCHITECTURE  = load_file('/etc/arch')
	VERSION       = load_file('/etc/version')    
	TEMP          = '/storage/.plexht/temp/'
	

class Updater(object):
	
	UPDATE_REQUEST_URL = "http://update.rasplex.com/update/updates.php"
	UPDATE_DOWNLOAD_URL = "http://sourceforge.net/projects/rasplex/files/autoupdate/%s/%s"
	LOCAL_UPDATE_DIR = "/storage/.update/"
	UPDATE_ARCHIVE = System.TEMP + "update.tar.gz"
		
	def _download(self, url):
		log("Updater._download: %s" % url)
		
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
		archive,m = urllib.urlretrieve(url, filename=self.UPDATE_ARCHIVE, reporthook=__reportProgress)
		if os.path.isfile(archive):
			return archive
		else:
			return None

	def _extract(self, archive):
		log("Updater._extract")
		def target_files(members):
			for tarinfo in members:
				if os.path.dirname(tarinfo.name).endswith("/target"):
					# remove dirname from name 
					tarinfo.name = os.path.basename(tarinfo.name)
					yield tarinfo

		showNotification("Extracting and installing files")		
		try:
			tar = tarfile.open(archive)
			tar.extractall(path=self.LOCAL_UPDATE_DIR, members=target_files(tar))
			tar.close()
		except tarfile.TarError, e:
			raise UpdateError("Extracting archive failed: %s" % e)


	def check_update(self, systemId=System.SYSTEMID):
		url = '%s?i=%s&d=%s&pa=%s&v=%s' % (self.UPDATE_REQUEST_URL, 
			systemId, 
			System.DISTRIBUTION, 
			System.ARCHITECTURE, 
			System.VERSION)

		request = urllib2.Request(url)
		response = urllib2.urlopen(request)
		update_json = response.read().strip()
		
		if update_json != "":
		   update_json = json.loads(update_json)
		
		   if 'data' in update_json and 'update' in update_json['data'] and 'folder' in update_json['data']:
			   # check if the release is newer than the current one
			   if System.VERSION not in update_json['data']['update']:
				   return update_json['data']
		return False

		
	def check_bleeding(self):
		return self.check_update("rasplex-update-check-bleeding")
				

	def do_update(self, data):
		log("Updater.do_update: %s" % json.dumps(data))
		if 'update' not in data or 'folder' not in data:
			log('Updater.do_update: Invalid update data')
			raise UpdateError("Invalid update data")

		# download
		url = self.UPDATE_DOWNLOAD_URL % (data['folder'], data['update'])

		if os.path.isfile(self.UPDATE_ARCHIVE):
			os.remove(self.UPDATE_ARCHIVE)
			
		archive = self._download(url)
		if not archive:
			raise UpdateError("Download failed")
				
		# install
		if not os.path.exists(self.LOCAL_UPDATE_DIR):
			os.makedirs(self.LOCAL_UPDATE_DIR)
		self._extract(archive)
		
		# cleanup
		if os.path.isfile(self.UPDATE_ARCHIVE):
			os.remove(self.UPDATE_ARCHIVE)



if (__name__ == "__main__"):
	import xbmcgui

	xbmcgui.Dialog().ok(__addonname__, "Update started", "This may take some time...")


	try:
		updater = Updater()
		update_data = None
				
		if __addon__.getSetting('VERSION') == "bleeding":
			update_data = updater.check_bleeding()
		else:			
			update_data = updater.check_update()
		
		# check if update is required
		if not update_data:
			xbmcgui.Dialog().ok(__addonname__, "No update required. (Current version: %s)" % System.VERSION)
		
		else:
			new_version = re.findall(r"\d+.\d+.\d+", update_data['update'])[0]
			showNotification("Updating to version %s" % new_version)
			
			updater.do_update(update_data)
			
			showNotification("Update prepared sucessfully. Please reboot to install.")
			ret = xbmcgui.Dialog().yesno(__addonname__, "Update prepared sucessfully", "A reboot is required to finish the installation.", "Reboot now?")
			if ret:
				xbmc.executebuiltin('Reboot')
		
	except UpdateError, e:
		showNotification("Update failed: %s" % e)
