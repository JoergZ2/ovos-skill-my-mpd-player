import sys
import os
import time
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
from ovos_workshop.intents import IntentBuilder
from lingua_franca.parse import extract_number
from ovos_backend_client.api import DeviceApi
from ovos_bus_client.session import SessionManager
from mpd import MPDClient
from mpd import CommandError as mce
from ovos_utils import classproperty
from ovos_utils.process_utils import RuntimeRequirements
from ovos_utils.log import LOG
mpcc = MPDClient()
##

class MyMpdPlaylist(OVOSSkill):
    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(internet_before_load=False,
                                   network_before_load=True,
                                   gui_before_load=False,
                                   requires_internet=False,
                                   requires_network=True,
                                   requires_gui=False,
                                   no_internet_fallback=False,
                                   no_network_fallback=False,
                                   no_gui_fallback=False)

    def initialize(self):
        DEFAULT_SETTINGS = {
            "__mycroft_skill_firstrun": "false",
            "radios": {
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
                "station_name_1": 0,
                "station_alt_name_1": 0,
                "station_name_2": 1
            }
        }
        self.settings.merge(DEFAULT_SETTINGS, new_only=True)
        self.settings_change_callback = self.on_settings_changed
        self.on_settings_changed()
        self.same_device = DeviceApi()
        self.uuid = self.same_device.uuid

    def on_settings_changed(self):
        self.radios = self.settings.get('radios')
        self.stations = self.settings.get('stations')
        self.translations = self.settings.get('translations')

    
#Basic MPD functions
    def open_connection(self, radio):
        host = self.radios[radio]['ip']
        port = self.radios[radio]['port'].replace("", "6600")
        eval(port)
        self.close_connection()
        try:
            mpcc.connect(host, port, timeout=10)
        except (ConnectionRefusedError):
            self.speak_dialog('mpd_not_running')
        except (OSError):
            self.speak_dialog('device_not_running')
        finally:
            pass
    
    def close_connection(self):
        mpcc.disconnect()
    
    def start_mpd(self, placement):
        self.open_connection(placement)
        mpcc.play()
        self.close_connection()

    def stop_mpd(self, placement):
        self.open_connection(placement)
        mpcc.stop()
        self.close_connection()

#Helper functions
#replaces device's IP if no placement has been spoken
#necessary for Hivemind clients
    def check_placement(self, location, placement=None):
        if location != None and placement != None:
            placement = placement.lower()
        if not placement:
            placement = location.lower()
        if not location:
            placement = placement.lower()
        result = self.radios.get(placement)
        if result != None:
            return placement
        else:
            self.speak_dialog('radio_error', {"radio": placement})
            return

    def extract_placement(self, message):
        sess = SessionManager.get(message)
        location = sess.site_id.lower()
        placement = message.data.get('placement', None)
        placement = self.check_placement(location, placement)
        return placement

#normalizing of station names
    def normalize_station(self,station):
        station = station.lower()
        station = station.replace(" ","_")
        return station

#fallback dialog if no device's placement is set (should work ;-))    
    def select_location(self):
        self.speak_dialog('where_to_play')
        #placement  = self.ask_selection(list(self.placements.keys()))
        placement  = self.ask_selection(['Büro', 'Werkstatt'])
        self.speak(placement)
        return placement

#transforms complex list/dictionary results to speakable text
    def eval_list(self, liste, query = None):
        answer = 0
        if not len(liste) == 0:
            for key in range(len(liste)):
                keys = liste[key].keys()
                pos = int(liste[key]['pos']) + 1
                if 'name' in keys:
                    name = liste[key]['name']
                    self.speak_dialog('query_found', {'pos': pos, 'name': name})
                    answer += 1
                    continue
                if 'title' in keys:
                    name = liste[key]['title']
                    self.speak_dialog('query_found', {'pos': pos, 'name': name})
                    answer += 1
                    continue
                else:
                    name = liste[key]['title']
                    self.speak_dialog('query_found', {'pos': pos, 'name': name})
                    answer += 1
        else:
            self.speak_dialog('query_not_found', {'query': query})
            answer = 0
        return answer

#adds all playlists to a complex list which will be evaluated by eval_list() 
    def merging_stored_lists(self, placement):
        self.open_connection(placement)
        pl = list(mpcc.listplaylists())
        a = []
        pl_dict = {}
        for key in range(len(pl)):
            pl_dict[pl[key]['playlist']] = mpcc.listplaylistinfo(pl[key]['playlist'])
            a.append(pl_dict)
        self.close_connection()
        return pl_dict

#creates a speakable answer from simple lists
    def create_answer_from_search_result(self, query, result_dict):
        answer = {'query': query}
        result = {'result': 'dummy'}
        a = ''
        for k1 in result_dict:
            pos = ''
            for k2 in range(len(result_dict[k1])):
                pos = pos + str(result_dict[k1][k2])
                if len(result_dict[k1])> 1 and k2 < len(result_dict[k1]) - 1: pos = pos + " und "
                if k2 == len(result_dict[k1]) - 1: pos = str(pos) + "; "
            a = a + "in " + k1 + " position " + pos
            result2 = {'result': a}
            result.update(result2)
        answer.update(result)
        return answer

#deletes a given playlist and adds selected titles from database search    
    def play_from_database_search(self, placement, playlist, pos):
        self.open_connection(placement)
        mpcc.clear()
        for i in range(len(playlist)):
            mpcc.add(playlist[i]['file'])
        mpcc.play(pos)
        self.close_connection()
    

#Current playlist functions names are self-explanatory
    def switch_to_next(self, placement):
        self.open_connection(placement)
        mpcc.next()
        self.close_connection()

    def switch_to_previous(self, placement):
        self.open_connection(placement)
        mpcc.previous()
        self.close_connection()

    def switch_to_first(self, placement):
        self.open_connection(placement)
        mpcc.play(0)
        self.close_connection()

    def switch_to_last(self, placement):
        self.open_connection(placement)
        result = mpcc.playlistinfo()
        playlist_length = len(result)
        pos = playlist_length - 1
        mpcc.play(pos)
        self.close_connection()

    def switch_to_pos(self, placement, pos):
        self.open_connection(placement)
        list_pos = int(pos)
        list_pos = list_pos -1
        mpcc.play(list_pos)
        self.close_connection()

    def switch_to_station(self,placement,pos):
        self.open_connection(placement)
        mpcc.play(pos)
        self.close_connection()

    def speak_current_title(self, placement):
        self.open_connection(placement)
        liste = mpcc.currentsong()
        if not 'artist' in liste:
            title = liste['title']
            pos = str(int(liste['pos']) + 1)
            end = "."
            self.speak_dialog('speak_current_title', {'pos': pos, 'title': title, 'end': end})
        else:
            title = liste['title']
            pos = str(int(liste['pos']) + 1)
            artist = liste['artist']
            end = "."
            self.speak_dialog('speak_current_title_artist', {'pos': pos, 'title': title, 'artist': artist, 'end': end})
        self.close_connection()

    def speak_current_list(self, placement):
        self.open_connection(placement)
        liste = mpcc.playlistinfo()
        answer = self.eval_list(liste)
        self.close_connection()
        return answer

#MPD volume functions - names are self-explanatory
    def vol_up(self, placement):
        self.open_connection(placement)
        mpcc.volume(+5)
        self.close_connection()

    def vol_down(self, placement):
        self.open_connection(placement)
        mpcc.volume(-5)
        self.close_connection()

    def set_vol(self, placement, vol):
        self.open_connection(placement)
        mpcc.setvol(vol)
        self.close_connection()

#Searching in current playlist
    def search_in_current_playlist(self, placement, query):
        try:
            self.open_connection(placement)
            tag = ['title', 'name', 'artist']
            needle = query
            result = []
            for key in tag:
                try:
                    result_new = mpcc.playlistsearch(key, str(needle))
                except Exception:
                    continue
                if not len(result_new) == 0:
                    result = result + result_new
            answer = self.eval_list(result, query)
            return answer
        except Exception as e:
            self.speak_dialog('error_in_function_current_playlist')
            return answer
        finally:
            self.close_connection()


#Stored playlists functions
    def list_stored_playlists(self, placement):
        try:
            self.open_connection(placement)
            list_playlist = mpcc.listplaylists()
        except Exception as e:
            LOG.info(str(e))
        finally:
            self.close_connection()
        names = ''
        key = 0
        while key < len(list_playlist):
            names = names + list_playlist[key]['playlist'] + ", " 
            key += 1
        return names

    def playlist_replace_and_play(self, placement, playlist, pos):
        playlist = playlist.lower()
        self.open_connection(placement)
        list_playlist = mpcc.listplaylists()
        for key in range(len(list_playlist)):
            curr_playlist = list_playlist[key]['playlist']
            if curr_playlist == playlist:
                result = list_playlist[key]['playlist']
                try:
                    mpcc.clear()
                    time.sleep(.5)
                    mpcc.load(result)
                    time.sleep(.5)
                    mpcc.play((int(pos) -1))
                    time.sleep(.5)
                except Exception as e:
                    LOG.info("Error: " + str(e))
                finally:
                    self.close_connection()
                break
            else:
                continue
#next function is deprecated but maybe reactivated sometime    
    def search_in_stored_playlists(self, placement, query):
        fields = ['title', 'name', 'artist']
        result = ''
        result_raw = {}
        value_result = []
        pl_dict = self.merging_stored_lists(placement)
        pl_names = list(pl_dict)
        for key1 in range(len(pl_names)):
            for key2 in range(len(pl_dict[pl_names[key1]])):
                for key3 in range(len(fields)):
                    if fields[key3] in pl_dict[pl_names[key1]][key2]:
                        if query.lower() in pl_dict[pl_names[key1]][key2][fields[key3]].lower():
                            line = (pl_dict[pl_names[key1]][key2])
                            pos = pl_dict[pl_names[key1]].index(line)
                            pos = pos + 1
                            value_result.append(pos)
                            key_result = pl_names[key1]
                            result_raw.update({key_result: value_result})
                            result = result_raw
                            print(result)
                        else:
                            pass
                    else:
                        pass
            value_result = []
        if len(result) != 0:
            answer = self.create_answer_from_search_result(query, result)
        else:
            self.speak_dialog('query_not_found', {'query': query})
        answer['result'] = answer['result'][:-2]; answer['result'] = answer['result'] + "."
        self.close_connection()
        return answer
    
#current function for searching in playlists
    def search_playlists_stored(self, placement, query, merged_playlists):
        results = 0
        keys1 = list(merged_playlists.keys())
        i1 = len(keys1)
        for k in range(i1):
            k_len = (len(merged_playlists[keys1[k]]))
            for k2 in range(k_len):
                    keys2 = list(merged_playlists[keys1[k]][k2].keys())
                    for k3 in range(len(keys2)):
                            if query.lower() in merged_playlists[keys1[k]][k2][keys2[k3]].lower():
                                result = merged_playlists[keys1[k]][k2][keys2[k3]]
                                if keys1[k]:
                                    playlist, query, pos, name = keys1[k], query, k2 +1, result
                                    self.speak_dialog('search_all_playlists', {'query': query, 'playlist': playlist, 'pos': pos, 'name': name})
                                    results = results + 1
                                    time.sleep(1)
                                break
        if results == 0:
            self.speak_dialog('term_not_found', {'query': query})

    
#Searches in database
    def search_in_database_and_play(self, placement, query, selection, pos):
        try:
            self.open_connection(placement)
            mpcc.clear()
            mpcc.searchadd(selection, query)
            if pos != "": pos = int(pos) -1
            if pos == None: pos = 0
            mpcc.play(pos)
        except:
            self.close_connection()
        finally:
            self.close_connection()

    def search_only_in_database(self, placement, query, selection):
        try:
            self.open_connection(placement)
            result = mpcc.search(selection, query)
            result_len = len(result)
            return (result, result_len)
        except:
            self.close_connection()
        finally:
            self.close_connection()

#Intent handlers
    @intent_handler('start_mpd.intent')
    def handle_start_mpd(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            self.start_mpd(placement)
        
    @intent_handler('stop_mpd.intent')
    def handle_stop_mpd(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            self.stop_mpd(placement)
     
    @intent_handler('pos5.intent')
    def handle_switch_to_pos(self, message):
        pos = message.data.get('pos')
        #pos = extract_number(pos); pos = int(pos)
        #pos = 5
        placement = self.extract_placement(message)
        LOG.info("Placement: " + str(placement))
        LOG.info("Position: " + str(pos))
        if placement != None:
            self.switch_to_pos(placement, pos)

    @intent_handler('pos_next.intent')
    def handle_pos_next(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            self.switch_to_next(placement)

    @intent_handler('pos_previous.intent')
    def handle_pos_previous(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            self.switch_to_previous(placement)

    @intent_handler('pos_first.intent')
    def handle_pos_first(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            self.switch_to_first(placement)

    @intent_handler('pos_last.intent')
    def handle_pos_last(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            self.switch_to_last(placement)

    @intent_handler('station_by_name.intent')
    def handle_station_by_name(self, message):
        sess = SessionManager.get(message)
        location = sess.site_id.lower()
        station = message.data.get('station')
        station = self.normalize_station(station)
        placement = self.extract_placement(message)
        if station in self.stations:
            pos = self.stations[station]
            self.switch_to_station(placement,pos)
        else:
            wrong_station = station
            self.speak_dialog('station_not_found', {'wrong_station': wrong_station})

    @intent_handler('vol_down.intent')
    def volume_down(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            self.vol_down(placement)

    @intent_handler('vol_up.intent')
    def volume_up(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            self.vol_up(placement)

    @intent_handler('vol_set_to.intent')
    def volume_set(self, message):
        placement = self.extract_placement(message)
        vol = message.data.get('pos_nr')
        vol = extract_number(vol); vol = int(vol)
        if placement != None:
            self.set_vol(placement, vol)

    @intent_handler('info_current_title.intent')
    def handle_speak_title(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            self.speak_current_title(placement)

    @intent_handler('playlist_stored.intent')
    def handle_list_stored_playlists(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            answer = self.list_stored_playlists(placement)
            self.speak(answer)
            playlist = self.get_response('which_playlist_to_play', num_retries=0)
            LOG.info(f"Playliste aus Listenansage: {playlist}")
            if playlist == None:
                self.speak_dialog('cancel')
                pass
            else:
                pos_nr = self.get_response('which_position_to_play', num_retries=1)
                LOG.info(f"Position: {pos_nr}")
                if pos_nr == None:
                    pos_nr = 1
                    self.speak_dialog('starting_with_number_one')
                    self.playlist_replace_and_play(placement, playlist, pos_nr)
                else:
                    self.playlist_replace_and_play(placement, playlist, pos_nr)

    @intent_handler('playlist_replace_and_play.intent')
    def handle_playlist_replace_and_play(self, message):
        playlist = message.data.get('playlist')
        pos = message.data.get('pos_nr')
        pos = extract_number(pos); pos = int(pos)
        placement = self.extract_placement(message)
        if placement != None:
            self.playlist_replace_and_play(placement, playlist, pos)

    @intent_handler('search.intent')
    def handle_search_current_playlist(self, message):
        placement = self.extract_placement(message)
        query = message.data.get('query')
        if placement != None:
            answer = self.search_in_current_playlist(placement, query)
            if answer != 0:
                play_title = self.ask_yesno('to_play')
                if play_title == 'yes':
                    pos_nr = self.get_response('which_position_to_play')
                    pos_nr = extract_number(pos_nr)
                    self.switch_to_pos(placement, pos_nr)
                elif play_title == 'no':
                    pass
                else:
                    self.speak_dialog('some_error')
            else:
                self.speak(answer)

    @intent_handler('search_all_playlists.intent')
    def handle_search_all_playlists(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            data = message.data; data = data.keys()
            query = message.data.get('query')
            merged_playlists = self.merging_stored_lists(placement)
            self.search_playlists_stored(placement, query, merged_playlists)

    @intent_handler('info_current_list.intent')
    def handle_speak_current_playlist(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            answer = self.speak_current_list(placement)
            self.speak(answer)

    @intent_handler('search_add_play_database.intent')
    def handle_search_in_database(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            query = message.data.get('query'); query_dict = {'query': query}
            pos_nr = message.data.get('pos_nr')
            pos_nr = extract_number(pos_nr);
            if pos_nr == "": pos_nr = '0'
            query_correct = self.ask_yesno('feedback_query', query_dict)
            if query_correct == 'yes':
                selection = self.get_response('which_data_field')
                selection = selection.lower()
                selection = self.translations[selection]
                if selection == "artist" or selection == "title" or selection == "album" or selection == "genre":
                    self.search_in_database_and_play(placement, query, selection, pos_nr)
                else: self.speak_dialog('missunderstand_selection')
            else:
                pass

    @intent_handler('search_in_database.intent')
    def handle_database_dialog(self, message):
        placement = self.extract_placement(message)
        if placement != None:
            query = message.data.get('query'); query_dict = {'query': query}
            if placement != None:
                query_correct = self.ask_yesno('feedback_query', query_dict)
                if query_correct == 'yes':
                    selection = self.get_response('which_data_field')
                    selection = selection.lower()
                    selection = self.translations[selection]
                    if selection == 'artist' or selection == 'title' or selection == 'album' or selection == 'genre':
                        search_result = self.search_only_in_database(placement, query, selection)
                        numbers_result = search_result[1]
                        if numbers_result != 0:
                            title = self.get_response('which_title_to_play', {'numbers': numbers_result})
                            if self.voc_match(title, 'nothing'):
                                pass
                            elif self.voc_match(title,'all'):
                                title = 0
                                self.play_from_database_search(placement, search_result[0], title)
                            else:
                                title = extract_number(title)
                                title = int(title) -1
                                self.play_from_database_search(placement, search_result[0], title)
                        else: self.speak_dialog('no_result', {'query': query, 'selection': selection})
                    else: self.speak_dialog('missunderstand_selection')
                else:
                    self.speak_dialog('missunderstand_query')
    

    def stop(self):
        pass

def create_skill():
    return MyMpdPlaylist()
