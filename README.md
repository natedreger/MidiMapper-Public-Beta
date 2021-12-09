# MidiMapper

I built MidiMapper to be a one stop shop for controlling various devices using USB MIDI keyboards or pads.  The intent is that this will run on a Raspberry Pi.

At it's most basic is a USB MIDI host to convert between USB keyboards and traditional 5-Pin MIDI. A 'thru' mode allows MIDI to pass directly from one device to another with minimal latency.

On a more advanced level MidiMapper allows keymaps to be created allowing note on commands to be converted to any of the following types:

- MIDI NOTE_ON (with channel)
- Program Change
- OSC command

MidiMapper also contains a builtin web interface for monitoring and setup.

Still To Do :
- [ ] Edit keymap via web interface
- [ ] Edit settings via web interface
- [x] Change midi mode via web interface
- [ ] Match mapping device control
- [ ] remove lag from mode change
-

Future features to implement :
- [ ] note to GPIO
- [ ] OSC to MIDI
- [ ] Channel Routing
- [ ] Device to Device mapping

Built with :
- python-rtmidi
- Flask-SocketIO
- Flask
- python-osc
