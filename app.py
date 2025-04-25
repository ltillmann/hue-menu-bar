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
        # init empty lights list and rooms tuple list
        self.listoflights = []
        self.rooms = []
        # dictionary to map submenu to parent's title
        self.parent_titles = {} 
        # icon display on menubar, automatically displays the icon black or white depending on menubar theme settings
        self.template = True
        self.icon = "icons/white.png"
        # menu items
        self.connection_status = rumps.MenuItem(icon="icons/bridge-v2-off.svg", title="Disconnected")
        self.quit = rumps.MenuItem(title='Quit', callback=rumps.quit_application)
        self.link = rumps.MenuItem(title="Connect Hue Bridge", callback = self.first_connect)
        self.room_buttons = {}
        self.light_buttons = {}

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
        groups = self.hue_bridge.get_group()
        self.rooms = [(group_id, group) for group_id, group in groups.items() if 'name' in group]
         
    # connect to Hue Bridge
    def connect_hue_bridge(self):
        # try to connect to bridge
        try:
            # init bridge API connection using local Bridge IP
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
                button_title = "Turn Off" if is_light_on else "Turn On"
                light_submenu = rumps.MenuItem(title=light_name)
                light_button = rumps.MenuItem(title=button_title, callback=self.set_lights)
                light_button.parent_light = light_name
                light_submenu.add(light_button)
                self.lights_menu.add(light_submenu)
                self.light_buttons[light_name] = light_button

        if self.rooms:
            self.rooms_menu = rumps.MenuItem(title="Rooms", icon="icons/rooms.svg")
            # create submenu for each room using self.rooms
            for group_id, group_data in self.rooms:
                room_name = group_data.get("name")
                is_room_on = group_data['action']['on']

                button_title = "Turn Off" if is_room_on else "Turn On"
                room_submenu = rumps.MenuItem(title=room_name)
                room_button = rumps.MenuItem(title=button_title, callback=self.set_rooms)
                room_button.parent_room_name = room_name
                room_button.parent_room_id = group_id
                room_submenu.add(room_button)
                self.rooms_menu.add(room_submenu)
                self.room_buttons[group_id] = room_button

        # Construct the rooms main menu
        if self.listoflights and not self.rooms:
            self.menu = [self.connection_status, None, self.lights_menu, None, self.quit]
        elif self.rooms and not self.listoflights:
            self.menu = [self.connection_status, None, self.rooms_menu, None, self.quit]
        elif self.listoflights and self.rooms:
            self.menu = [self.connection_status, None, self.lights_menu, self.rooms_menu, None, self.quit]
        else:
            pass
    
    def update_lights_menu(self):
        # refresh listoflights
        self.get_lights()
      
        for light_name in self.listoflights:
            # check if light is already on, returns true/false
            is_light_on = self.hue_bridge.get_light(light_name, 'on')
            button_title = "Turn Off" if is_light_on else "Turn On"
            self.light_buttons[light_name].title = button_title

    def update_rooms_menu(self):
        # refresh self.rooms
        self.get_rooms()
        for group_id, group_data in self.rooms:
            is_room_on = group_data['action']['on']
            button_title = "Turn Off" if is_room_on else "Turn On"
            if group_id in self.room_buttons:
                self.room_buttons[group_id].title = button_title

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
        callback = sender.title
        if callback == "Turn Off": 
            self.hue_bridge.set_group(parent_roomname, 'on', False)
        else:
            self.hue_bridge.set_group(parent_roomname, 'on', True)
        # refresh menu
        self.update_rooms_menu()

### Main
if __name__ == "__main__":
    HueControllerApp().run()