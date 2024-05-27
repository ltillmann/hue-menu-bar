#!/usr/bin/env python3

### imports
import rumps
from phue import Bridge, PhueRegistrationException
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
import time
import socket
import os
import subprocess


### helper functions
def get_path(filename: str):
    # Get the path of the current Python script
    current_file_path = os.path.dirname(__file__)
    file_path = os.path.join(current_file_path, filename)

    return file_path



### HueBridge multicast DNS service discovery
class HueBridgeListener(ServiceListener):

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} updated")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} removed")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)

        if info and "hue bridge" in info.name.lower():
            # attribute binary IP as a dots-and-numbers format string
            self.bridge_ip = socket.inet_ntoa(info.addresses[0]) 


            
### HueController rumps App
class HueControllerApp(rumps.App):
    def __init__(self, _):
        super(HueControllerApp, self).__init__("")
        rumps.debug_mode(True)

        self.quit_button = None

        # init empty lights and rooms lists 
        self.listoflights = []
        self.listofrooms = []
        
        # dictionary to map submenu to parent's title
        self.parent_titles = {} 
        
        # icon display on menubar, automatically displays the icon black or white depending on menubar theme settings
        self.template = True
        self.icon = "icons/white.png"

        self.connection_status = rumps.MenuItem(icon="icons/bridge-v2-off.svg", title="Disconnected")
        self.quit = rumps.MenuItem(title='Quit', callback=rumps.quit_application)
        self.link = rumps.MenuItem(title="Connect Hue Bridge", callback = self.first_connect)

        self.build_init_menu()
        
        # try to autoconnect with bridge
        try:
            self.autoconnect()
        # when no internet connection
        except TimeoutError as e:
            rumps.alert(f"Connection timed out!\n\nPlease ensure stable Internet connection.", icon_path="icons/bridge-v2-off.svg")
        # when no ip yet
        except FileNotFoundError:
            pass

 
    def is_new_network(self):
        pass


    def test_internet_connection(self, bridge_ip, timeout):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect((bridge_ip, 80))  # bridge ip and default port 80
                    return True
            except Exception:
                continue
        return False
            
    
    def store_data(self):
        p = os.path.join(os.getenv("HOME"), ".huemenubar")
        if not os.path.exists(p):
            os.makedirs(p)
        with open(os.path.join(p, "bridge_ip.txt"), "w") as output_file:
            output_file.write(self.hue_bridge_ip)


    def build_init_menu(self):
            self.menu = [self.connection_status, None, self.link, None, self.quit]
    
    
    def build_lights_menu(self):
        # when lights registered to bridge
        if self.listoflights:
            self.lights_menu = rumps.MenuItem(title="Lights", icon="icons/lights.svg")

            # Create submenu for each light
            for light_name in self.listoflights:
                # check if light is already on, returns true/false
                is_light_on = self.hue_bridge.get_light(light_name, 'on')

                # build light menuitem
                light_submenu = rumps.MenuItem(title=light_name)

                # define button title and create button
                button_title = "Turn Off" if is_light_on else "Turn On"
                onoff_button = rumps.MenuItem(title=button_title, callback=self.on_off_lights)
                
                # attribute lightname to button
                onoff_button.parent_light = light_name

                # Add button to light menuitem
                light_submenu.add(onoff_button)  
                # Add light menuitem to lights menu
                self.lights_menu.add(light_submenu)

        if self.listofrooms:
            self.rooms_menu = rumps.MenuItem(title="Rooms", icon="icons/rooms.svg")
            # Create submenu for each room
            for idx, room_name in enumerate(self.listofrooms, start=1):
                # check if room is already on, returns true/false
                is_room_on = self.hue_bridge.get_group(idx, 'on')

                # build light menuitem
                room_submenu = rumps.MenuItem(title=room_name)

                # define button title and create button
                button_title = "Turn Off" if is_room_on else "Turn On"
                onoff_button = rumps.MenuItem(title=button_title, callback=self.on_off_rooms)
                
                # attribute lightname and id to button
                onoff_button.parent_room_name = room_name
                onoff_button.parent_room_id = idx

                # Add button to light menuitem
                room_submenu.add(onoff_button)  
                # Add light menuitem to lights menu
                self.rooms_menu.add(room_submenu)



        # Construct the rooms main menu
        if self.listoflights and not self.listofrooms:
            self.menu = [self.connection_status, None, self.lights_menu, None, self.quit]

        elif self.listofrooms and not self.listoflights:
            self.menu = [self.connection_status, None, self.rooms_menu, None, self.quit]
        
        elif self.listoflights and self.listofrooms:
            self.menu = [self.connection_status, None, self.lights_menu, self.rooms_menu, None, self.quit]



    def on_off_lights(self, sender):
        # Find the parent title of the sender (submenu)
        parent_lightname = sender.parent_light
        callback = sender.title

        if callback == "Turn Off": 
            print(f"Turning {parent_lightname} Off")
            self.hue_bridge.set_light(parent_lightname, 'on', False)

        else:
            print(f"Turning {parent_lightname} On")
            self.hue_bridge.set_light(parent_lightname, 'on', True)

        # refresh menu
        self.menu.clear()
        self.build_lights_menu()



    def on_off_rooms(self, sender):
        # Find the parent title and id of the sender
        parent_roomname = sender.parent_room_name
        parent_roomid = sender.parent_room_id
        callback = sender.title

        if callback == "Turn Off": 
            print(f"Turning {parent_roomname} Off")
            self.hue_bridge.set_group(parent_roomid, 'on', False)

        else:
            print(f"Turning {parent_roomname} On")
            self.hue_bridge.set_group(parent_roomid, 'on', True)

        # refresh menu
        self.menu.clear()
        self.build_lights_menu()


    ## autodetects hue bridge IP and devices
    def detect_hue_bridge(self):
        # detect bridge in local network via multicast DNS service discovery
        listener = HueBridgeListener()
        zeroconf_instance = Zeroconf()
        ServiceBrowser(zeroconf_instance, "_hue._tcp.local.", listener)

        # Wait for a few seconds to allow time for discovery
        time.sleep(1)

        # close instance
        zeroconf_instance.close()

        # try to detect bridge on local network and store ip
        try:
            self.hue_bridge_ip = listener.bridge_ip
            self.store_data()
            return True
        
        except Exception as e:
            print(e)
            return False
            
                
    def first_connect(self, _):
        # try to detect hue bridge ip on local network
        # when hue bridge ip was detected
        if self.detect_hue_bridge() is True:
            rumps.notification("Success", "", f"Hue Bridge found at {self.hue_bridge_ip}", icon="icons/bridge-v2.svg")
            time.sleep(2)
            # try to connect
            self.connect_hue_bridge()
        # if no bridge detected
        else:
            print("No Hue Bridge found on local network")
            rumps.notification("Error", "", "No Hue Bridge found on local network", icon="icons/bridge-v2-off.svg")


    def autoconnect(self):     
        # check if hue bridge ip exists
        p = os.path.join(os.getenv("HOME"), ".huemenubar", "bridge_ip.txt")
        if os.path.exists(p):
            # read ip and try to connect if exists
            with open(p, "r") as text_file:
                self.hue_bridge_ip = text_file.read()
            
            # check if internet connection exists
            if self.test_internet_connection(self.hue_bridge_ip, timeout=15) is True:
                # connect
                self.connect_hue_bridge()
            else:
                raise TimeoutError()
        else:
            raise FileNotFoundError()
    

    ## Connect to Hue Bridge
    def connect_hue_bridge(self):
        # try to connect to bridge
        try:
            # init bridge API connection uisng Bridge ip
            self.hue_bridge = Bridge(self.hue_bridge_ip)
            self.hue_bridge.connect()


            # get list of light names registered on bridge
            self.listoflights = list(self.hue_bridge.get_light_objects(mode='name').keys())

            # get list of room name registered to bridge
            self.listofrooms = [room['name'] for room in self.hue_bridge.get_group().values()]


            #refresh menu bar 
            self.menu.clear()
            self.build_lights_menu()
            self.connection_status.icon = "icons/bridge-v2.svg"
            self.connection_status.title = " Bridge Connected"
            
            rumps.notification("", "", "Hue Bridge Connected", icon="icons/bridge-v2.svg")

        # if device wasn't authenticated to bridge yet
        except PhueRegistrationException as e:
            rumps.alert("Authentication needed!\n\nPlease push the Link Button on your Hue Bridge before connecting.", icon_path="icons/button.svg")

        # generic exception
        except Exception as e:
            rumps.alert(f"Connection could not be established!\n\nException: {e}", icon_path="icons/bridge-v2-off.svg")
            


### run
if __name__ == "__main__":
    HueControllerApp("HueController").run()