from setuptools import setup

APP = ['src/app.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['speech_recognition'],
    'plist': {
        'NSMicrophoneUsageDescription': 'This application needs access to the microphone to listen for the activation command.'
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)