from setuptools import setup
import os

def get_path(filename: str):
    # Get the path of the current Python script
    current_file_path = os.path.dirname(__file__)
    file_path = os.path.join(current_file_path, filename)

    return file_path

APP = ['app.py']
DATA_FILES = [('icons', [get_path('icons/white.png'), get_path('icons/button.svg'), get_path('icons/bridge-v2.svg'), get_path('icons/bridge-v2-off.svg'), get_path('icons/lights.svg'), get_path('icons/rooms.svg')])]
OPTIONS = {
    
    'argv_emulation': False,
    'plist': {
        'LSUIElement': True,
    },
    'packages': ['rumps', 'zeroconf', 'phue'],
    'iconfile': 'icons/huebar.icns',
}

setup(
    name='HueBar',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
