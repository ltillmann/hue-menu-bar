HueController macOS Menu Bar App
=================================

Overview
--------
HueController is a macOS menu bar application for controlling Philips Hue lights. It provides a simple interface for managing lights and rooms directly from the menu bar.

![Alt text](/screenshots/example_usage.png?raw=true)

Features
--------
- Automatic detection of Philips Hue Bridge devices on the local network.
- Displays connection status to the Hue Bridge in the menu bar.
- Allows users to turn lights and rooms on or off.
- Persistence: Remembers the IP address of the last connected Hue Bridge.

Installation
------------
As a python script:
1. Clone or download the repository to your local machine.
2. Install the necessary Python libraries using pip:

    ```
    pip install -r requirements.txt
    ```

3. Run the `main.py` script:

    ```
    python main.py
    ```

As a standalone application:
1. Install Py2App
2. Build the app using the setup.py file

    ```
    python setup.py py2app
    ```
3. Launch application by double-clicking or via Terminal
4. (Optional) Add application to your Login Items to launch on system startup

Usage
-----
- Launch the application.
- On first start, the local machine has to be authenticated to Hue Bridge by pushing the Link button before connecting.
- It will attempt to connect to the Philips Hue Bridge automatically.
- If successful, the connection status will be displayed in the menu bar.
- Control lights and rooms directly from the menu bar.

Credits
-------
- rumps: https://github.com/jaredks/rumps
- phue: https://github.com/studioimaginaire/phue
- zeroconf: https://github.com/jstasiak/python-zeroconf
- hass-hue-icons: https://github.com/arallsopp/hass-hue-icons

License
-------
This project is licensed under the MIT License - see the LICENSE file for details.

