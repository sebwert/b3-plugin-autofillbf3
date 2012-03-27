# -*- coding: utf-8 -*-
#
# AutoFill BF3 Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2012 Sebastian Ewert (me@sebastian-ewert.de)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#

__version__ = '0.1'
__author__ = 'Sebastian Ewert'

import b3
import b3.events
from b3.plugin import Plugin
from ConfigParser import NoOptionError

class Autofillbf3Plugin(Plugin):
    def __init__(self, console, config=None):
        self._admin_plugin = None
        self.console = console
        #check if round is active or not
        self._active = False
        self._server_size = 4
        Plugin.__init__(self, console, config)
################################################################################################################
#
# Plugin interface implementation
#
################################################################################################################
    def onLoadConfig(self):
        """\
This is called after loadConfig(). Any plugin private variables loaded
from the config need to be reset here.
"""
        self.verbose('Loading Autofill Config')
        self._loadServerSize()


    def startup(self):
        """\
Initialize plugin settings
"""
        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
            return False
        # Register our events
        self.registerEvent(b3.events.EVT_GAME_ROUND_START)
        self.registerEvent(b3.events.EVT_GAME_ROUND_END)
        self.registerEvent(b3.events.EVT_CLIENT_DISCONNECT)
        self.registerEvent(b3.events.EVT_CLIENT_JOIN)
        
    def onEvent(self, event):
        """\
Handle intercepted events
"""
        if event.type == b3.events.EVT_GAME_ROUND_START:
            self.debug('Gameround started set active to true and adjust slots')
            self._active = True
            self._adjustSlots()
        if event.type == b3.events.EVT_GAME_ROUND_END:
            self.debug('Gameround end setting active false and maxPlayers to maximum size')
            self._adjustSlots(True)
            self._active = False
        if (event.type == b3.events.EVT_CLIENT_DISCONNECT 
                or event.type == b3.events.EVT_CLIENT_JOIN):
            self._adjustSlots()
        
################################################################################################################
#
# Privat Stuff
#
################################################################################################################
    def _loadServerSize(self):
        """\
Load server_size config field 
"""
        try:
            self._server_size = int(self.config.get('preferences', 'server_size'))
        except NoOptionError:
            self.info('No config option \"preferences\\server_size\" found. Using default value : %s' % self._server_size)
        except ValueError, err:
            self.debug(err)
            self.warning('Could not read level value from config option \"preferences\\server_size\". Using default value \"%s\" instead. (%s)' % (self._server_size, err))
        except Exception, err:
            self.error(err)
        self.info('server_size is %s' % self._server_size)
    def _adjustSlots(self, max_slots = False):
        """\
adjust slots according to rules and current logged in user
"""
        if not self._active:
            self.debug("self.active is %s do not adjust player slots" % self._active)
            return True
        if(max_slots):
            self._setSlots(self._server_size)
        else:
            count_players = len(self.console.clients.getList())
            if count_players == 0:
                self._setSlots(self._server_size)
            elif count_players < self._server_size - 2:
                #minimum 4 players
                self._setSlots(max(4, count_players + 2))
            else:
                self.debug("No slots changed, online/serversize  %s/%s" % (count_players, self._server_size))
    def _setSlots(self, count):
        """\
set server slots to count
"""
        now_slots = int(self.console.getCvar('maxPlayers').value)
        if(now_slots == count):
            self.debug("No slots changed, setting/wanted %s/%s" % (now_slots, count))
            return True
        else:
            try:
                self.console.setCvar('maxPlayers', count)
            except Exception, err:
                self.error(err)
            else:
                self.debug("maxPlayers set to %s" % count)
if __name__ == '__main__':
    from b3.config import XmlConfigParser
    from b3.fake import fakeConsole
    from b3.fake import joe, simon, moderator, superadmin, reg, admin
    import time
    config = XmlConfigParser() 
    config.load('conf/plugin_autofillbf3.xml')
    event_start = type('lamdbaobject', (object,), {'type' :  b3.events.EVT_GAME_ROUND_START})()
    event_end = type('lamdbaobject', (object,), {'type' :  b3.events.EVT_GAME_ROUND_END})()
    event_join = type('lamdbaobject', (object,), {'type' :  b3.events.EVT_CLIENT_JOIN})()
    event_leave = type('lamdbaobject', (object,), {'type' :  b3.events.EVT_CLIENT_DISCONNECT})()
    p = Autofillbf3Plugin(fakeConsole, config)
    p.console.setCvar('maxPlayers', 18)
    
    p.onStartup()
    p.onLoadConfig()
    
    p.onEvent(event_start)
    joe.connects(cid = 1)
    p.onEvent(event_join)
    simon.connects(cid = 2)
    p.onEvent(event_join)
    moderator.connects(cid = 3)
    p.onEvent(event_join)

    p.onEvent(event_end)
    superadmin.connects(cid=4)
    joe.disconnects()
    p.onEvent(event_leave)
    p.onEvent(event_start)
    joe.connects(cid = 1)
    p.onEvent(event_join)
    joe.disconnects()
    p.onEvent(event_leave)

