from glob import glob
from random import choice
from functools import partial

from kivy.core.audio import SoundLoader

from kivyx.widgets import Widget
from utils.misc import separate_thread


class SoundPlayer(Widget):
    """Superclass for sound players with sound event handling."""
    sound_cache = {}

    def on_stop(self, sound, *args):
        """Default handler."""
        pass

    def on_start(self, sound, *args):
        """Default handler."""
        pass


class SoundFXPlayer(SoundPlayer):
    """A sound effects player that plays various sounds at a time."""

    def __init__(self):
        SoundPlayer.__init__(self)
        self.playing = []

        self.register_event_type("on_stop")
        self.register_event_type("on_start")

    def load_sound(self, filename, use_cache=True):
        if use_cache and filename in SoundFXPlayer.sound_cache:
            return SoundFXPlayer.sound_cache[filename]

        sound = SoundLoader.load(filename)

        if use_cache:
            SoundFXPlayer.sound_cache[filename] = sound

        return sound

    @separate_thread
    def play(self, filename, use_cache=True, volume=1.0):
        sound = self.load_sound(filename, use_cache=use_cache)

        if sound is None:
            return

        self.playing.append(sound)

        sound.volume = volume
        sound.play()
        sound.bind(on_stop=partial(self.stop, sound))

        self.dispatch("on_start", sound)

    def stop(self, sound, *args):
        if sound.state != "stop":
            sound.stop()

        if sound in self.playing:
            self.playing.remove(sound)

        self.dispatch("on_stop", sound)


class MusicPlayer(SoundPlayer):
    """A music player that plays only one music at a time."""

    def __init__(self):
        SoundPlayer.__init__(self)
        self.playing = None

        self.register_event_type("on_stop")
        self.register_event_type("on_start")

    def load_sound(self, filename, use_cache=True):
        if use_cache and filename in MusicPlayer.sound_cache:
            return MusicPlayer.sound_cache[filename]

        sound = SoundLoader.load(filename)

        if use_cache:
            MusicPlayer.sound_cache[filename] = sound

        return sound

    @separate_thread
    def play(self, filename, use_cache=True, volume=1.0):
        if self.playing is not None:
            self.stop()

        self.playing = self.load_sound(filename, use_cache=use_cache)

        if self.playing is None:
            return

        self.playing.volume = volume
        self.playing.play()
        self.playing.bind(on_stop=self.stop)

        self.dispatch("on_start", self.playing)

    def stop(self, *args):
        if self.playing is None:
            return

        if self.playing.state != "stop":
            self.playing.stop()

        self.dispatch("on_stop", self.playing)
        self.playing = None


class ShuffleMusicPlayer(MusicPlayer):
    def __init__(self, sound_directory, extension, volume=1.0):
        MusicPlayer.__init__(self)
        self.sound_directory = sound_directory
        self.extension = extension
        self._volume = volume
        self.sound_player = MusicPlayer()

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value

        if self.sound_player.playing is not None:
            self.sound_player.playing.volume = value

    def start(self):
        if self.sound_player.playing is not None:
            return

        self.sound_player.bind(on_stop=self._play_random)
        self._play_random()

    def stop(self):
        if self.sound_player.playing is not None:
            self.sound_player.unbind(on_stop=self._play_random)
            self.sound_player.stop()

    def _play_random(self, *args):
        if self.sound_player.playing is None:
            filename = choice(glob(self.sound_directory + self.extension))
            self.sound_player.play(filename, volume=self.volume)
