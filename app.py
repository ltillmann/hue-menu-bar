#!/usr/bin/env python3

### imports
import rumps
from phue import Bridge, PhueRegistrationException
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
import time
import socket
import os



### HueBridge multicast DNS service discovery
class HueBridgeListener(ServiceListener):
    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info and "hue bridge" in info.name.lower():
            # attribute binary IP as a dots-and-numbers format string
            self.bridge_ip = socket.inet_ntoa(info.addresses[0]) 


            
### HueController rumps App
class HueControllerApp(rumps.App):
    def __init__(self):
        super(HueControllerApp, self).__init__("")
        rumps.debug_mode(True)

        self.quit_button = None
        self.is_connected = False
        # init empty lights and rooms lists 
        self.listoflights = []
        self.listofrooms = []
        # dictionary to map submenu to parent's title
        self.parent_titles = {} 
        # icon display on menubar, automatically displays the icon black or white depending on menubar theme settings
        self.template = True
        self.icon = "icons/white.png"
        # menu items
        self.connection_status = rumps.MenuItem(icon="icons/bridge-v2-off.svg", title="Disconnected")
        self.quit = rumps.MenuItem(title='Quit', callback=rumps.quit_application)
        self.link = rumps.MenuItem(title="Connect Hue Bridge", callback = self.first_connect)

        # build menu
        self.build_init_menu()
        
        # try to autoconnect with bridge
        try:
            self.autoconnect()
        # when no internet connection
        except TimeoutError as e:
            rumps.alert(f"Connection timed out!\n\nPlease ensure stable Internet connection.", icon_path="icons/bridge-v2-off.svg")
        # when no IP yet
        except FileNotFoundError:
            pass

        # device synchronization
        @rumps.timer(5)
        def refresh_menu(sender):
            # Refresh menu
            if self.is_connected == True:
                #self.menu.clear()
                self.update_lights_menu()
                self.update_rooms_menu()

    @staticmethod
    def get_path(filename: str):
        # Get the path of the current Python script
        current_file_path = os.path.dirname(__file__)
        file_path = os.path.join(current_file_path, filename)
        return file_path
    
    @staticmethod
    def store_data(hue_bridge_ip):
        p = os.path.join(os.getenv("HOME"), ".huemenubar")
        if not os.path.exists(p):
            os.makedirs(p)
        with open(os.path.join(p, "bridge_ip.txt"), "w") as output_file:
            output_file.write(hue_bridge_ip)

    def build_init_menu(self):
                self.menu = [self.connection_status, None, self.link, None, self.quit]

    def autoconnect(self):     
        # check if hue bridge ip exists
        ip_path = os.path.join(os.getenv("HOME"), ".huemenubar", "bridge_ip.txt")
        if os.path.exists(ip_path):
            # read ip and try to connect if exists
            with open(ip_path, "r") as text_file:
                self.hue_bridge_ip = text_file.read()
            # check if internet connection exists
            if self.test_internet_connection(self.hue_bridge_ip, timeout=15) is True:
                # connect
                self.connect_hue_bridge()
            else:
                raise TimeoutError()
        else:
            raise FileNotFoundError()
        
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
    
    def detect_hue_bridge(self):
        # detect bridge in local network via multicast DNS service discovery
        listener = HueBridgeListener()
        zeroconf_instance = Zeroconf()
        ServiceBrowser(zeroconf_instance, "_hue._tcp.local.", listener)
        # Wait for a few seconds to allow time for discovery
        time.sleep(4)
        # close instance
        zeroconf_instance.close()
        # try to detect bridge on local network and store ip
        try:
            self.hue_bridge_ip = listener.bridge_ip
            self.store_data(self.hue_bridge_ip)
            return True
        except Exception as e:
            return False
            
    def first_connect(self):
        # try to detect hue bridge ip on local network
        # when hue bridge ip was detected
        if self.detect_hue_bridge() is True:
            rumps.notification("Success", "", f"Hue Bridge found at IP: {self.hue_bridge_ip}", icon="icons/bridge-v2.svg")
            time.sleep(2)
            # try to connect
            self.connect_hue_bridge()
        # if no bridge detected
        else:
            rumps.notification("Error", "", "No Hue Bridge found on local network. Check internet/VPN settings and make sure Bridge is powered on.", icon="icons/bridge-v2-off.svg")
    

    def get_lights(self):
        # get list of light names registered on bridge
        self.listoflights = list(self.hue_bridge.get_light_objects(mode='name').keys())
        
    def get_rooms(self):
        # get list of room name registered to bridge
        self.listofrooms = [room['name'] for room in self.hue_bridge.get_group().values()]
         
    # connect to Hue Bridge
    def connect_hue_bridge(self):
        # try to connect to bridge
        try:
            # init bridge API connection uisng Bridge ip
            self.hue_bridge = Bridge(self.hue_bridge_ip)
            self.hue_bridge.connect()
            self.is_connected = True
            
            # get lights
            self.get_lights()
            # get rooms
            self.get_rooms()

            # build menu bar 
            self.menu.clear()
            self.build_lights_menu()
            self.connection_status.icon = "icons/bridge-v2.svg"
            self.connection_status.title = "Bridge Connected"
            rumps.notification("", "", "Hue Bridge Connected", icon="icons/bridge-v2.svg")

        # if device wasn't authenticated to bridge yet
        except PhueRegistrationException as e:
            rumps.alert("Authentication needed!\n\nPlease push the Link Button on your Hue Bridge before connecting.", icon_path="icons/button.svg")
        # generic exception
        except Exception as e:
            rumps.alert(f"Connection could not be established!\n\nException: {e}", icon_path="icons/bridge-v2-off.svg")
    
    def build_lights_menu(self):
        # when lights registered to bridge
        if self.listoflights:
            self.lights_menu = rumps.MenuItem(title="Lights", icon="icons/lights.svg")
            # create submenu for each light
            for light_name in self.listoflights:
                # check if light is already on, returns true/false
                is_light_on = self.hue_bridge.get_light(light_name, 'on')
                # build light menuitem
                self.light_submenu = rumps.MenuItem(title=light_name)
                # define button title and create button
                button_title = "Turn Off" if is_light_on else "Turn On"
                self.on_off_lights_button = rumps.MenuItem(title=button_title, callback=self.set_lights)
                # attribute lightname to button
                self.on_off_lights_button.parent_light = light_name
                # Add button to light menuitem
                self.light_submenu.add(self.on_off_lights_button)  
                # Add light menuitem to lights menu
                self.lights_menu.add(self.light_submenu)

        if self.listofrooms:
            self.rooms_menu = rumps.MenuItem(title="Rooms", icon="icons/rooms.svg")
            # create submenu for each room
            for idx, room_name in enumerate(self.listofrooms, start=1):
                # check if room is already on, returns true/false
                is_room_on = self.hue_bridge.get_group(idx, 'on')
                # build light menuitem
                self.room_submenu = rumps.MenuItem(title=room_name)
                # define button title and create button
                button_title = "Turn Off" if is_room_on else "Turn On"
                self.on_off_rooms_button = rumps.MenuItem(title=button_title, callback=self.set_rooms)
                # attribute lightname and id to button
                self.on_off_rooms_button.parent_room_name = room_name
                self.on_off_rooms_button.parent_room_id = idx
                # Add button to light menuitem
                self.room_submenu.add(self.on_off_rooms_button)  
                # Add light menuitem to lights menu
                self.rooms_menu.add(self.room_submenu)

        # Construct the rooms main menu
        if self.listoflights and not self.listofrooms:
            self.menu = [self.connection_status, None, self.lights_menu, None, self.quit]
        elif self.listofrooms and not self.listoflights:
            self.menu = [self.connection_status, None, self.rooms_menu, None, self.quit]
        elif self.listoflights and self.listofrooms:
            self.menu = [self.connection_status, None, self.lights_menu, self.rooms_menu, None, self.quit]
        else:
            pass
    
    def update_lights_menu(self):
        for light_name in self.listoflights:
            # check if light is already on, returns true/false
            is_light_on = self.hue_bridge.get_light(light_name, 'on')
            button_title = "Turn Off" if is_light_on else "Turn On"
            self.on_off_lights_button.title = button_title

    def update_rooms_menu(self):
        for idx, room_name in enumerate(self.listofrooms, start=1):
            # check if room is already on, returns true/false
            is_room_on = self.hue_bridge.get_group(idx, 'on')
            button_title = "Turn Off" if is_room_on else "Turn On"
            self.on_off_rooms_button.title = button_title

    def set_lights(self, sender):
        # get parent title of sender (submenu)
        parent_lightname = sender.parent_light
        callback = sender.title
        if callback == "Turn Off": 
            self.hue_bridge.set_light(parent_lightname, 'on', False)
        else:
            self.hue_bridge.set_light(parent_lightname, 'on', True)
        # refresh menu
        self.update_lights_menu()

    def set_rooms(self, sender):
        # get parent title and id of sender
        parent_roomname = sender.parent_room_name
        parent_roomid = sender.parent_room_id
        callback = sender.title
        if callback == "Turn Off": 
            self.hue_bridge.set_group(parent_roomid, 'on', False)
        else:
            self.hue_bridge.set_group(parent_roomid, 'on', True)
        # refresh menu
        self.update_rooms_menu()

### Main
if __name__ == "__main__":
    HueControllerApp().run()