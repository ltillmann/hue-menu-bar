Hue Controller macOS X Menu Bar Application
=================================

Overview
--------
Hue Controller is a macOS X menu bar application for controlling Philips Hue lights. It provides a minimal interface for managing lights and rooms directly from the menu bar.

![Alt text](/screenshots/example_usage.png?raw=true)

Features
--------
- Automatic detection of Philips Hue Bridge devices on the local network.
- Displays connection status to the Hue Bridge in the menu bar.
- Allows users to turn lights and rooms on or off.
- Remembers the IP address of the last connected Hue Bridge and auto-connects on reboot.
- Multi-device light status synchronization

Installation
------------
As a python script:
1. Clone or download the repository to your local machine.
2. Install the necessary Python libraries using pip:

    ```
    pip install -r requirements.txt
    ```

3. Run the `app.py` script:

    ```
    python3 app.py
    ```

As a standalone application:
1. Install Py2App
2. Build the app using the preconfigured setup.py file

    ```
    python3 setup.py py2app
    ```
3. Launch application by double-clicking app or open via Terminal.
4. (Optional) Move application to application folder and add to Login Items to launch on system startup.

Usage
-----
- Launch application/run script.
- On first start, the local machine has to be authenticated to Hue Bridge by pushing the Link button before clicking connect.
- Otherwise, it will attempt to connect to the Philips Hue Bridge automatically.
- If successful, the connection status and your lights/rooms will be displayed in the menu bar.
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

