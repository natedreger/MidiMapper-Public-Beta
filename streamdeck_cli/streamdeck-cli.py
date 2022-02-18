#!./venv/bin/python3

#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# Example script showing basic library usage - updating key images with new
# tiles generated at runtime, and responding to button state change events.

import os
import sys
import json
import threading
from subprocess import Popen
import shlex

import api
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Devices import StreamDeck
from typing import Dict, Tuple, Union, cast, Callable

decks: Dict[str, StreamDeck.StreamDeck] = {}

# Folder location of image assets used by this example.
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")

class Dimmer:
    timeout = 0
    brightness = -1
    brightness_dimmed = -1
    __stopped = False
    __dimmer_brightness = -1
    __timer = None
    __change_timer = None

    def __init__(
        self,
        timeout: int,
        brightness: int,
        brightness_dimmed: int,
        brightness_callback: Callable[[int], None],
    ):
        """ Constructs a new Dimmer instance

        :param int timeout: The time in seconds before the dimmer starts.
        :param int brightness: The normal brightness level.
        :param Callable[[int], None] brightness_callback: Callback that receives the current
                                                          brightness level.
         """
        self.timeout = timeout
        self.brightness = brightness
        self.brightness_dimmed = brightness_dimmed
        self.brightness_callback = brightness_callback

    def stop(self) -> None:
        """ Stops the dimmer and sets the brightness back to normal. Call
        reset to start normal dimming operation. """
        if self.__timer:
            self.__timer.stop()

        if self.__change_timer:
            self.__change_timer.stop()

        self.__dimmer_brightness = self.brightness
        self.brightness_callback(self.brightness)
        self.__stopped = True

    def reset(self) -> bool:
        """ Reset the dimmer and start counting down again. If it was busy dimming, it will
        immediately stop dimming. Callback fires to set brightness back to normal."""

        self.__stopped = False
        if self.__timer:
            self.__timer.stop()

        if self.__change_timer:
            self.__change_timer.stop()

        if self.timeout:
            self.__timer = QTimer()
            self.__timer.setSingleShot(True)
            self.__timer.timeout.connect(partial(self.change_brightness))
            self.__timer.start(self.timeout * 1000)

        if self.__dimmer_brightness != self.brightness:
            previous_dimmer_brightness = self.__dimmer_brightness
            self.brightness_callback(self.brightness)
            self.__dimmer_brightness = self.brightness
            if previous_dimmer_brightness < 10:
                return True

        return False

    def dim(self, toggle: bool = False):
        """ Manually initiate a dim event.
            If the dimmer is stopped, this has no effect. """

        if self.__stopped:
            return

        if toggle and self.__dimmer_brightness == 0:
            self.reset()
        elif self.__timer and self.__timer.isActive():
            # No need for the timer anymore, stop it
            self.__timer.stop()

            # Verify that we're not already at the target brightness nor
            # busy with dimming already
            if self.__change_timer is None and self.__dimmer_brightness:
                self.change_brightness()

    def change_brightness(self):
        """ Move the brightness level down by one and schedule another change_brightness event. """
        if self.__dimmer_brightness and self.__dimmer_brightness >= self.brightness_dimmed:
            self.__dimmer_brightness = self.__dimmer_brightness - 1
            self.brightness_callback(self.__dimmer_brightness)
            self.__change_timer = QTimer()
            self.__change_timer.setSingleShot(True)
            self.__change_timer.timeout.connect(partial(self.change_brightness))
            self.__change_timer.start(10)
        else:
            self.__change_timer = None


dimmers: Dict[str, Dimmer] = {}

# Generates a custom tile with run-time generated text and custom image via the
# PIL module.
def render_key_image(deck, icon_filename, font_filename, label_text):
    # Resize the source image asset to best-fit the dimensions of a single key,
    # leaving a margin at the bottom so that we can draw the key title
    # afterwards.
    icon = Image.open(icon_filename)
    image = PILHelper.create_scaled_image(deck, icon, margins=[0, 0, 20, 0])

    # Load a custom TrueType font and use it to overlay the key index, draw key
    # label onto the image a few pixels from the bottom of the key.
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_filename, 14)
    draw.text((image.width / 2, image.height - 5), text=label_text, font=font, anchor="ms", fill="white")

    return PILHelper.to_native_format(deck, image)


# Returns styling information for a key based on its position and state.
def get_key_style(deck, key, state):
    # Last button in the example application is the exit button.
    exit_key_index = deck.key_count() - 1

    if key == exit_key_index:
        name = "exit"
        icon = "{}.png".format("Exit")
        font = "Roboto-Regular.ttf"
        label = "Bye" if state else "Exit"
    else:
        name = "emoji"
        icon = "{}.png".format("Pressed" if state else "Released")
        font = "Roboto-Regular.ttf"
        label = "Pressed!" if state else "Key {}".format(key)

    return {
        "name": name,
        "icon": os.path.join(ASSETS_PATH, icon),
        "font": os.path.join(ASSETS_PATH, font),
        "label": label
    }


# Creates a new key image based on the key index, style and current key state
# and updates the image on the StreamDeck.
def update_key_image(deck, page, key, state):
    deck_id = deck.get_serial_number()
    # Determine what icon and label to use on the generated key.
    key_style = get_key_style(deck, key, state)

    # Generate the custom key with the requested image and label.
    icon = api.get_button_icon(deck_id, page, key)
    if icon == '':
        icon = key_style['icon']
    label = api.get_button_text(deck_id, page, key)
    image = render_key_image(deck, icon, key_style["font"], label)

    # Use a scoped-with on the deck to ensure we're the only thread using it
    # right now.
    with deck:
        # Update requested key with the generated image.
        deck.set_key_image(key, image)


# Prints key state change information, updates rhe key image and performs any
# associated actions when a key is pressed.
def key_change_callback(deck, key, state):
    deck_id = deck.get_serial_number()
    page = api.get_page(deck_id)
    update_key_image(deck, page, key, state)
    internal_command = {}
    external_command = {}
    external_commands = ['OSC', 'MIDI', 'MQTT']
    print(deck_id, key, state)
    if state:
        # if dimmers[deck_id].reset():
        #     return


        if api.get_button_command_type(deck_id, page, key) in external_commands:
            external_command = {"command_type":api.get_button_command_type(deck_id, page, key), "command_string":api.get_button_command_string(deck_id, page, key)}
        else:
            internal_command = {"command_type":api.get_button_command_type(deck_id, page, key), "command_string":api.get_button_command_string(deck_id, page, key)}

        if external_command:
            # queue.put(external_command)
            # print(f"External: {external_command}")
            print(json.dumps(external_command), file = sys.stdout)

        if internal_command:
            # print(f"Internal: {internal_command}")

            command = internal_command['command_type'] == 'Command'
            if command:
                try:
                    Popen(shlex.split(internal_command['command_string']))
                except Exception as error:
                    print(f"The command '{internal_command['command_string']}' failed: {error}")

            keys = internal_command['command_type'] == 'Keystroke'
            if keys:
                keys = internal_command['command_string']
                keys = keys.strip().replace(" ", "")
                for section in keys.split(","):
                    # Since + and , are used to delimit our section and keys to press,
                    # they need to be substituted with keywords.
                    section_keys = [_replace_special_keys(key_name) for key_name in section.split("+")]

                    # Translate string to enum, or just the string itself if not found
                    section_keys = [
                        getattr(Key, key_name.lower(), key_name) for key_name in section_keys
                    ]

                    for key_name in section_keys:
                        if isinstance(key_name, str) and key_name.startswith("delay"):
                            sleep_time_arg = key_name.split("delay", 1)[1]
                            if sleep_time_arg:
                                try:
                                    sleep_time = float(sleep_time_arg)
                                except Exception:
                                    print(f"Could not convert sleep time to float '{sleep_time_arg}'")
                                    sleep_time = 0
                            else:
                                # default if not specified
                                sleep_time = 0.5

                            if sleep_time:
                                try:
                                    time.sleep(sleep_time)
                                except Exception:
                                    print(f"Could not sleep with provided sleep time '{sleep_time}'")
                        else:
                            try:
                                keyboard.press(key_name)
                            except Exception:
                                print(f"Could not press key '{key_name}'")

                    for key_name in section_keys:
                        if not (isinstance(key_name, str) and key_name.startswith("delay")):
                            try:
                                keyboard.release(key_name)
                            except Exception:
                                print(f"Could not release key '{key_name}'")

            write = internal_command['command_type'] == "Text"
            if write:
                try:
                    keyboard.type(internal_command['command_string'])
                except Exception as error:
                    print(f"Could not complete the write command: {error}")

            # Set absolute brightness
            set_brightness = internal_command['command_type'] == 'Set Brightness'
            if set_brightness:
                try:
                    api.set_brightness(deck_id, int(internal_command['command_string']))
                    dimmers[deck_id].brightness = api.get_brightness(deck_id)
                    dimmers[deck_id].reset()
                except Exception as error:
                    print(f"Could not change brightness: {error}")

            # Dim by percentage
            change_brightness = internal_command['command_type'] == 'Brightness'
            if set_brightness:
                try:
                    api.change_brightness(deck_id, int(internal_command['command_string']))
                    dimmers[deck_id].brightness = api.get_brightness(deck_id)
                    dimmers[deck_id].reset()
                except Exception as error:
                    print(f"Could not change brightness: {error}")

            switch_page = internal_command['command_type'] == 'Page'
            if switch_page:
                api.set_page(deck_id, int(internal_command['command_string']) - 1)

            CloseStreamDeck = internal_command['command_type'] == 'CloseStreamDeck'
            if CloseStreamDeck:
                api.close_decks()
                sys.exit()
# # #
# def key_change_callback(deck, key, state):
#     # Print new key state
#     print("Deck {} Key {} = {}".format(deck.id(), key, state), flush=True)
#
#     # Update the key image based on the new key state.
#     update_key_image(deck, key, state)
#
#     # Check if the key is changing to the pressed state.
#     if state:
#         key_style = get_key_style(deck, key, state)
#
#         # When an exit button is pressed, close the application.
#         if key_style["name"] == "exit":
#             # Use a scoped-with on the deck to ensure we're the only thread
#             # using it right now.
#             with deck:
#                 # Reset deck, clearing all button images.
#                 deck.reset()
#
#                 # Close deck handle, terminating internal worker threads.
#                 deck.close()


if __name__ == "__main__":
    streamdecks = DeviceManager().enumerate()

    print("Found {} Stream Deck(s).\n".format(len(streamdecks)))

    for index, deck in enumerate(streamdecks):
        deck.open()
        deck.reset()
        deck_id = deck.get_serial_number()
        decks[deck_id] = deck
        items = decks.items()
        for deck_id, deck in items:
            print(deck_id)

        print("Opened '{}' device (serial number: '{}')".format(deck.deck_type(), deck.get_serial_number()))

        # Set initial screen brightness to 30%.
        deck.set_brightness(30)

        # Register callback function for when a key state changes.
        deck.set_key_callback(key_change_callback)
        api.render(decks)
        # Wait until all application threads have terminated (for this example,
        # this is when all deck handles are closed).
        for t in threading.enumerate():
            try:
                t.join()
            except RuntimeError:
                pass
