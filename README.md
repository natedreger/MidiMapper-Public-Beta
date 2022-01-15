# MidiMapper

VERY MUCH A BETA!

I built MidiMapper to be a one stop shop for controlling various devices using USB MIDI keyboards or pads.  I'm running this as a daemon on a Raspberry PI 4 to provide a stand alone solution.

At it's most basic is a USB MIDI host to convert between USB keyboards and traditional 5-Pin MIDI. A 'thru' mode allows MIDI to pass directly from one device to another with minimal latency.

On a more advanced level MidiMapper allows keymaps to be created allowing note on commands to be converted to any of the following types:

- MIDI NOTE_ON (with channel)
- Program Change
- OSC command
- MQTT

MidiMapper also contains a builtin web interface for monitoring and setup.

Still To Do :
- [ ] loop connection attempts
- [x] Rotating logs
- [x] GUI for log management
- [x] Edit keymap via web interface
- [x] Edit settings via web interface
- [x] Change midi mode via web interface
- [x] Match mapping device control
- [x] remove lag from mode change
- [x] encrypt passwords in settings file


Known Issues to fix :
- [ ] knowndevices error if file not exist
- [x] i\o list not reloading on rescan\restart (settings not pushing???)
- [ ] match device check on apply_settings
- [ ] apply settings not right
- [ ] rescan midi I/O results in corrupt data upon next note (for now midi will be restarted)
- [ ] keymap edit only works when output selected
- [x] quit dialog box triggers on cancel
- [x] settings['match_device'] getting set 'on' not true somewhere
- [x] web PC not sending in mapped mode
- [x] ValueError: 'dummy message' is not in list
- [x] match device not working
- [x] keymap gui not working

Future features to implement :
- [ ] note to GPIO
- [ ] Channel Routing
- [ ] Device to Device mapping
- [x] OSC to MIDI
- [X] Logs


Built using :
- python-rtmidi
- python-socketio==5.5.0
- Flask==2.0.2
- python-osc==1.8.0
- Flask-SocketIO==5.1.1
- python-dotenv==0.19.2
- requests==2.22.0
- simple-websocket==0.5.0
- websocket-client==1.2.3


OSC input examples:
- /MIDI/note_on/1/55/127
- /MIDI/program_change/2/17
- /OSC/host_machine.local/8000/Qlab/go
