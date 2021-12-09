# MidiMapper

I built MidiMapper to be a one stop shop for controlling various devices using USB MIDI keyboards or pads.

At it's most basic is a USB MIDI host to convert between USB keyboards and traditional 5-Pin MIDI. A 'thru' mode allows MIDI to pass directly from one device to another with minimal latency.

On a more advanced level MidiMapper allows keymaps to be created allowing note on commands to be converted to any of the following :

- [x] transform one note to any other note
- [x] note to program change 
- [x] note to OSC

Still ToDo :
- [ ] Edit keymap via web interface
- [ ] Edit settings via web interface

Future features to implement :
- [ ] note to GPIO
- [ ] OSC to MIDI


