Autofill Battlefield 3 for Big Brother Bot
==========================================

Description
-----------

This plugin changes the available slots according to the acctual
connected player. The idea behind this is to get more quickmatch user.

The initial forum thread can be found at:
http://forum.bigbrotherbot.net/battle-field-3/script-for-server-filling/


Installation
------------

- copy extplugins stuff into b3/extplugins
- add to the plugins section of your main b3 config file: 
```<plugin name="autofillbf3" config="@b3/extplugins/conf/plugin_autofillbf3.xml" />```


Config file
-----------

server_size
    put here the max size of your server

min_slots
    slots will not decrease further than this value

slots_when_empty
    if last user leaves your server the slots will be set to this value


Support
-------

http://forum.bigbrotherbot.net/releases/autofill-plugin-for-battlefield-3/


Changelog
---------

0.1
    basic functionality, listens for join, leave, round end, round
    start events and adjusts slots
