Autofill Battlefield 3 for Big Brother Bot
==========================================

Description
-----------

This plugin changes the available slots according to the acctual
connected player. The idea behind this is to get more quickmatch user.

The initial forum thread can be found at:
http://forum.bigbrotherbot.net/battle-field-3/script-for-server-filling/

 - The available slots will always be 2 more than the connected player.
 - If ``adjust_start_restart_payer_count`` is set to ``On`` in config it will
   change roundStartPlayerCount/roundRestartPlayerCount to 8/4 after the
   round started and set it to 1/0 when the round ends.
 - If ``change_maps`` is set to ``On`` and you have two map files and 
   write their correct absolute pathes to ``maps_many``, ``maps_few`` 
   this plugin will change your map rotation when the number of connected user
   falls under/growth over your ``maps_border``


 Installation
------------

- copy extplugins stuff into b3/extplugins
- add to the plugins section of your main b3 config file: 
``<plugin name="autofillbf3" config="@b3/extplugins/conf/plugin_autofillbf3.xml" />``


Config file
-----------

server_size
    put here the max size of your server

min_slots
    slots will not decrease further than this value

slots_when_empty
    if last user leaves your server the slots will be set to this value

adjust_start_restart_payer_count
    ''On/Off'' if enabled the roundStartPlayerCount/roundRestartPlayerCount
    will be changed on rounf start and end

change_maps
    ''On/Off'' enables map according to the connected user

maps_many
    absolute path to your map file when many users connected

maps_few
    absolute path to your map file when few users connected

maps_border
    If less than this Number of user are connected maps_few is used

Map Files:
~~~~~~~~~~

At this time it is important, that your map file does not contain any empty lines
or any lines with another beginning as "mapname gamemode rounds". Only the 
battlefield 3 server map names are allowed!

MP_003 ConquestSmall0 1         #Theran Highway
The line above is allowd cause the parser will stop after the number of rounds. 
There you can write comments

#Theran Highway  MP_003 ConquestSmall0 1
The line above will lead to an error cause the parser is not able to recognise
that the first element is not the map name

You should have recieved a ``maps.dist`` file and a ``maps.all.txt`` file with 
this plugin. The maps.dist file is an example of how an maps file could look like.
No empty lines and the fomat described above. The maps.all.txt file is a file with
all combinations of game modes and map names that are allowed in battlefield 3 at the
time. please have a speacial look at the expansion set maps.

Support
-------

Support will only be given at the bigbrother forum:
http://forum.bigbrotherbot.net/releases/autofill-plugin-for-battlefield-3


Support
-------

http://forum.bigbrotherbot.net/releases/autofill-plugin-for-battlefield-3/


Changelog
---------

0.1
    basic functionality, listens for join, leave, round end, round
    start events and adjusts slots
0.2
    add mechanism to change roundStartPlayerCount/roundRestartPlayerCount
0.3
    add automatic map change according to connected player

