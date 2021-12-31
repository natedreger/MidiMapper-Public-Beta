#!/usr/bin/env python
#
# probe_ports.py
#
"""Shows how to probe for available MIDI input and output ports."""

from rtmidi import (API_LINUX_ALSA, API_MACOSX_CORE, API_RTMIDI_DUMMY,
                    API_UNIX_JACK, API_WINDOWS_MM, MidiIn, MidiOut,
                    get_compiled_api)

try:
    input = raw_input
except NameError:
    # Python 3
    StandardError = Exception

apis = {
    API_LINUX_ALSA: "Linux ALSA",
    API_RTMIDI_DUMMY: "Rtmidi Dummy"
}

available_apis = get_compiled_api()

def probe_ports():
    for api, api_name in sorted(apis.items()):
        if api in available_apis:
            for name, class_ in (("input", MidiIn), ("output", MidiOut)):
                try:
                    midi = class_(api)
                    ports = midi.get_ports()
                except StandardError as exc:
                    print("Could not probe MIDI %s ports: %s" % (name, exc))
                    continue

                if not ports:
                    print("No MIDI %s ports found." % name)
                else:
                    print(f'!!!!!!!!!!!! {name} {ports} !!!!!!!!!!')
                    print("<<<<< Available MIDI %s ports: >>>>>>\n" % name)

                    for port, name in enumerate(ports):
                        print("[%i] %s" % (port, name))

                print('')
                del midi

def getAvailableIO(class_):
    for api, api_name in sorted(apis.items()):
        if api in available_apis:
            midi = class_(api)
            return midi.get_ports()
            del midi
