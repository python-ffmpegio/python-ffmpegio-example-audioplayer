from time import sleep
import ffmpegio
import pyaudio
from pprint import pprint
from contextlib import contextmanager

from testfile_generator import testfiles


@contextmanager
def pyaudio_stream(
    rate, channels, width=None, unsigned=False, format=None, *args, **kwargs
):
    p = pyaudio.PyAudio()

    if format is None:
        if width is None:
            raise ValueError("Either width or format must be specified.")
        format = p.get_format_from_width(width, unsigned)

    try:
        stream = p.open(rate, channels, format, *args, **kwargs)
        try:
            stream.start_stream()
            yield stream
            stream.stop_stream()
        finally:
            stream.close()
    finally:
        p.terminate()


ar = 44100  # playback sampling rate
ac = 2  # number of channels
width = 2  # signed 2-byte integer format
sample_fmt = "s16"

with testfiles(1) as files:
    file = files[0]

    # open ffmpegio's stream-reader to read nblk samples at a time
    with ffmpegio.open(file, "ra", sample_fmt=sample_fmt, ac=ac, ar=ar) as f:

        # define callback (2)
        def callback(_, nblk, *__):
            # read nblk samples from the ffmpeg and pass it onto pyaudio
            data = f.read(nblk)["buffer"]
            return (data, pyaudio.paContinue)

        with pyaudio_stream(
            rate=ar,
            channels=ac,
            width=width,
            output=True,
            stream_callback=callback,
        ) as stream:

            # wait for stream to finish
            while stream.is_active():
                sleep(0.1)
