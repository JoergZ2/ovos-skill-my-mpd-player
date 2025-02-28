# <img src="https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/list.svg" card_color="#22A7F0" width="50" height="50" style="vertical-align:bottom"/>
# ovos-skill-my-mpd-player
OVOS skill to control MPD instances
This OVOS skill tries to make the handling of saved playlists for the player MPD comfortable. In addition, this skill occasionally dialogs with the user or announces information. It is strongly recommended to disable the internal OVOS preference for media usage (ovos-common-play-plugin) because it hinders the use of own media skills.
If you can answer three or more questions with yes, you should try this skill:<br>
Are different playlists used in MPD?<br>
Is there more than one MPD player in the local network?<br>
Is there more than one OVOS system (Hivemind satellites) in the house / apartment?<br>
Do you want to be able to control all MPD players with all OVOS systems?
To my knowledge, no other skills offer these possibilities.

## Example sentences:
[alternative phrases are marked thus (term 2 | term 3)]
"Turn on the radio" or "Turn on the radio in the kitchen (bedroom | workshop | …)" provided that the MPD software is already running but not currently playing a file or stream.<br>
"Turn the radio a little louder/lower" or "Set the volume to 50" <br>
"Play station (title | position) one (two | three | ..)" - if the player is in the same room<br>
"Play station (title | position) one (two | three | ..) on the radio in (the ) kitchen (bedroom | workshop)"<br>
"Play the first (next | previous | last) track (station | ...)"<br>
"What am I listening to right now?"<br>
"What playlists are there?" After that a dialog is shown to ask for list and start position<br>
"Open the playlist radio stations (or another existing playlist) and play station three" - direct specification of playlist and start position<br>
"Which songs (titles | songs | stations) are in the current playlist (list)"<br>
"What playlists are there?"<br>
"Search (Find | Exists) [search term] in the current playlist." - Search the current playlist<br>
"Search (Find | Exists) [search term] in any playlist." - Search all playlists<br>
"Search (Find | Exists) [search term] in the music database (music collection)." - then dialog for narrowing down search results.<br>
All commands can be executed on a remote device with the addition "on the radio (in the | in the) [room name]".

Seems to be deprecated: To avoid possible conflicts with the skill ovos-skill-volume, the announcement to change the volume must be expressed in a differentiated way. The best results are (for an english speaking german) with this words "Turn up (down) the volume of mpd (in the kitchen)". At least a blacklisting of ovos-skill-volume helps but is not necessary. Also, the general ovos-skill controls the master volume of the soundcard whereas the volume control of the mpd skill controls the output level of the MPD server.
Please read at least the configuration section in the wiki.<br>

## Installation
In virtualenv: ```pip install git+https://github.com/JoergZ2/ovos-skill-my-mpd-player```
In Docker container ovos_core from host ```docker exec ovos_core pip install git+https://github.com/JoergZ2/ovos-skill-my-mpd-player``` or with a Docker management environment using the internal console with the command line from virtualenv.

## Configuration
At least there are two sections or main keys to configure the skill: "radios" and "stations". The first key is a stamdard OVOS key.
"radios" contains as much sub-keys as there are MPD instances to control. Each radi jey has the (spoken) name as main key and IP address and an optional key for a non standard port. If port is left empty standard port 6600 is used.
"stations" is a key which is filled witcgh an dictionary of (spoken) station names and a position number from playlist. Note that the first position is 0 and not 1. You can use different names for the same postion if the station is known under different names. For transparency I left my private radio stations playlist in zhis README.md. Station names which have more than one word should be written with underline.
```
{
    "__mycroft_skill_firstrun": false,
    "radios": {
        "büro": {
            "ip": "192.168.178.90",
            "port": ""
        },
        "werkstatt": {
            "ip": "192.168.178.29",
            "port": ""
        },
        "server1": {
            "ip": "IP_1",
            "port": ""
        },
        "server2": {
            "ip": "IP_2",
            "port": ""
        }
    },
    "stations": {
        "deutschlandfunk": 0,
        "dlf": 0,
        "deutschlandfunk_kultur": 1,
        "nova": 2,
        "deutschlandfunk_nova": 2,
        "dlf_nova": 2,
        "ndr_1": 3,
        "ndr_2": 4,
        "ndr_90_3": 5,
        "ndr_info": 6,
        "ndr_kultur": 7,
        "station_name_2": 1
    }
}
```
## Requirements
python-mpd2 (`pip install python-mpd2`)

## Credits
JoergZ2

## Category
**Music & Audio**

## Tags
#Mpd, playlist, mycroft, skills

