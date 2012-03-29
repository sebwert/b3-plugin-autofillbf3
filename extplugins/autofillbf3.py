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
__version__ = '0.3.1'
__author__ = 'Sebastian Ewert'

if __name__ == '__main__':
    import sys
    sys.path.append('../../../source')

import b3
import b3.events
from b3.plugin import Plugin
from ConfigParser import NoOptionError
from b3.parsers.frostbite2.protocol import CommandFailedError

class Autofillbf3Plugin(Plugin):
    def __init__(self, console, config=None):
        self._admin_plugin = None
        self.console = console
        #check if round is active or not
        self._active = False
        self._server_size = 16
        self._slots_when_empty = 16
        self._min_slots = 4
        #change roundStart/RestartPlayerCount
        self._do_rs = True
        self._do_change_maps = False
        self._do_end_round = True
        self._maps = {'many' : [], 'few' : []}
        self._maps_many = ''
        self._maps_few = ''
        self._maps_current_played = ''
        self._maps_load_error = {'few' : True, 'many' : True}
        self._border_many = 10
        self._border_few = 5
        self._maps_parsed = False
        Plugin.__init__(self, console, config)
################################################################################################################
#
# plugin interface implementation
#
################################################################################################################
    def onLoadConfig(self):
        """
        This is called after loadConfig(). Any plugin private variables loaded
        from the config need to be reset here.
        """
        self.verbose('Loading Autofill Config')
        self._loadServerSize()
        self._loadMinSlots()
        self._loadSlotsWhenEmpty()
        self._loadDoRS()
        self._loadMaps()


    def startup(self):
        """
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
        """
        Handle intercepted events
        """
        if event.type == b3.events.EVT_GAME_ROUND_START:
            self._doRoundStart()
        if event.type == b3.events.EVT_GAME_ROUND_END:
            self._doRoundEnd()
        if event.type == b3.events.EVT_CLIENT_DISCONNECT:
            self._doUserLeave()
        if event.type == b3.events.EVT_CLIENT_JOIN:
            self._doUserJoin()
################################################################################################################
#
# config loading
#
################################################################################################################
    def _doLoadVar(self, config_name, variable_name, func_suff = ""):
        """
        Load config name from config and save as self.variable_name
        func_suff is for self.config.get + func_suff
        """
        try:
            vars(self)[variable_name] = getattr(self.config, 'get' + func_suff)('preferences', config_name)
        except NoOptionError:
            self.info('No config option \"preferences\\%s\" found. Using default value : %s' % (config_name, getattr(self, variable_name)))
        except ValueError, err:
            self.debug(err)
            self.warning('Could not read level value from config option \"preferences\\%s\". Using default value \"%s\" instead. (%s)' % (config_name, getattr(self, variable_name), err))
        except Exception, err:
            self.error(err)
        self.info('%s is %s' % (config_name, getattr(self, variable_name)))
    
    
    def _loadDoRS(self):
        self._doLoadVar('adjust_start_restart_payer_count', '_do_rs', 'boolean')
    def _loadSlotsWhenEmpty(self):
        self._doLoadVar('slots_when_empty', '_slots_when_empty', 'int')
    def _loadMinSlots(self):
        self._doLoadVar('min_slots', '_min_slots', 'int')
    def _loadServerSize(self):
        self._doLoadVar('server_size', '_server_size', 'int')
    def _loadMaps(self):
        self._doLoadVar('change_maps', '_do_change_maps', 'boolean')
        self._doLoadVar('end_round_last_player_left', '_do_end_round', 'boolean')
        self._doLoadVar('maps_many', '_maps_many')
        self._doLoadVar('maps_few', '_maps_few')
        self._doLoadVar('border_many', '_border_many', 'int')
        self._doLoadVar('border_few', '_border_few', 'int')
        #check if many is really more than few
        if self._border_few > self._border_few:
            hold_many = self._border_many
            self._border_many = self._border_few
            self._border_few = hold_many
            del hold_many
################################################################################################################
#
# event wrapper functions
#
################################################################################################################
    def _doRoundStart(self):
        self.debug('Gameround started set active to true and adjust slots')
        self._active = True
        self._adjustSlots()
        if self._do_rs:
            self._setRS(8, 4)
    def _doRoundEnd(self):
        self.debug('Gameround end setting active false and maxPlayers to maximum size')
        self._adjustSlots(True)
        self._active = False
        if self._do_rs:
            self._setRS(1, 0)
    def _doUserJoin(self):
        self._adjustSlots()
        self._handleMaps()
    def _doUserLeave(self):
        self._adjustSlots()
        self._handleMaps()
################################################################################################################
#
# adjust server slots an start/restart stuff 
#
################################################################################################################
    def _adjustSlots(self, max_slots = False):
        """
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
                self._setSlots(self._slots_when_empty)
            elif count_players < self._server_size - 2:
                #minimum 4 players
                self._setSlots(max(self._min_slots, count_players + 2))
            else:
                self.debug("No slots changed, online/serversize  %s/%s" % (count_players, self._server_size))
    def _setSlots(self, count):
        """
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
    def _setRS(self, s, rs):
        """
        set s for vars.roundStartPlayerCount
        and rs for vars.roundRestartPlayerCoun
        """
        try:
            self.console.setCvar('roundStartPlayerCount', s)
        except Exception, err:
            self.error(err)
        else:
            self.debug("roundStartPlayerCount set to %s" % s)
        try:
            self.console.setCvar('roundRestartPlayerCount', rs)
        except Exception, err:
            self.error(err)
        else:
            self.debug("roundRestartPlayerCount set to %s" % rs)
################################################################################################################
#
# handle maps stuff
#
################################################################################################################
    def _handleMaps(self):
        if not self._do_change_maps:
            self.debug('_do_change_maps is %s map change aborted' % self._do_change_maps)
            return True
        #parse maps if not already parsed or forced to parse
        if not self._maps_parsed:
            self._parseMaps()
        count_players = len(self.console.clients.getList())
        #If las player left end round
        if count_players == 0 and self._do_end_round:
            try:
                self.console.write(('mapList.endRound', 1))
            except CommandFailedError, e:
                self.error('mapList.endRound: %s' %  e.message)
            else:
                self.debug('Last Player left so end Round')
        if count_players > self._border_many and self._maps_current_played == 'few':
            self._setMaps('many')
        elif count_players < self._border_few and self._maps_current_played == 'many':
            self._setMaps('few')
        else:
                self.debug('NO MAP LOADED: Loaded maps are %s, connected players %s, border_many %s, border_few %s' % (self._maps_current_played, count_players, self._border_many, self._border_few))

    def _setMaps(self, map_type):
        #exit if there was an error parsing this map type
        if self._maps_load_error[map_type]:
            self.debug('setMaps abortet because off previous map file error')
            return True
        try:
            self.console.write(('mapList.clear',))
        except CommandFailedError, e:
            self.error('mapList.clear error, NO MAPS ADDED: %s' % e.message)
        else:
            self.debug('mapList cleared')
            for map in self._maps[map_type]:
                try:
                    self.console.write(('mapList.add', map[0], map[1], map[2]))
                except CommandFailedError, e:
                    self.error('mapList.add: %s/%s/%s: %s' % (map[0], map[1], map[2], e.message))
                else:
                    self.debug('mapList.add: %s/%s/%s' % (map[0], map[1], map[2]))
                    self._maps_current_played = map_type
            try:
                self.console.write(('mapList.setNextMapIndex', 0))
            except CommandFailedError, e:
                self.error('mapList.setNextMapIndex: %s' % e.message)
    def _parseMaps(self):
        try:
            file_many = open(self._maps_many, "r").readlines()
        except IOError:
            self.error('can not open file "%s"' % self._maps_many)
            self._maps_load_error['many'] = True
        else:
            for line in file_many:
                self._maps['many'].append(line.split(' ', 3))
            self._maps_load_error['many'] = False
            self.debug('File %s succesfully opened' % file_many)
        try:
            file_few = open(self._maps_few, "r").readlines()
        except IOError:
            self.error('can not open file "%s"' % self._maps_few)
            self._maps_load_error['few'] = True
        else:
            for line in file_few:
                self._maps['few'].append(line.split(' ', 3))
            self._maps_load_error['few'] = False
            self.debug('File %s succesfully opened' % file_few)
        if not self._maps_load_error['many'] and not self._maps_load_error['few']:
            self._maps_parsed = True
            self.info('There was at least one error opening your map files many/few %s/%s' % (self._maps_load_error['many'], self._maps_load_error['few']))
################################################################################################################
#
# Debuging, Testing
#
################################################################################################################


if __name__ == '__main__':
    from b3.config import XmlConfigParser
    from b3.fake import fakeConsole
    from b3.fake import joe, simon, moderator, superadmin, reg, admin
    import time
    config = XmlConfigParser() 
    config.load('conf/plugin_autofillbf3.xml.test')
    event_start = type('lamdbaobject', (object,), {'type' :  b3.events.EVT_GAME_ROUND_START})()
    event_end = type('lamdbaobject', (object,), {'type' :  b3.events.EVT_GAME_ROUND_END})()
    event_join = type('lamdbaobject', (object,), {'type' :  b3.events.EVT_CLIENT_JOIN})()
    event_leave = type('lamdbaobject', (object,), {'type' :  b3.events.EVT_CLIENT_DISCONNECT})()
    p = Autofillbf3Plugin(fakeConsole, config)
    p.console.setCvar('maxPlayers', 18)
    p.onStartup()
    p.onLoadConfig()
    """  Adjust slot size
    
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
    """
    """ change map """
    
    p.onEvent(event_start)
    joe.connects(cid = 1)
    simon.connects(cid = 2)
    moderator.connects(cid = 3)
    p.onEvent(event_join)
    superadmin.connects(cid=4)
    p.onEvent(event_join)
    reg.connects(cid=5)
    p.onEvent(event_join)

    joe.disconnects()
    p.onEvent(event_leave)
    moderator.disconnects()
    p.onEvent(event_leave)
    superadmin.disconnects()
    p.onEvent(event_leave)
    reg.disconnects()
    p.onEvent(event_leave)
    simon.disconnects()
    p.onEvent(event_leave)

