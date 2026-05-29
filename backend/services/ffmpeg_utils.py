import os
import shutil

_UNSET = object()
_FFMPEG_PATH: str | object = _UNSET


def get_ffmpeg_path() -> str | None:
    """Resolve ffmpeg: system PATH first, then bundled binary from imageio-ffmpeg."""
    global _FFMPEG_PATH
    if _FFMPEG_PATH is not _UNSET:
        return _FFMPEG_PATH or None

    system = shutil.which("ffmpeg")
    if system:
        _FFMPEG_PATH = system
        return system

    try:
        import imageio_ffmpeg

        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled and os.path.isfile(bundled):
            _FFMPEG_PATH = bundled
            return bundled
    except Exception:
        pass

    _FFMPEG_PATH = ""
    return None


def is_ffmpeg_available() -> bool:
    return get_ffmpeg_path() is not None
