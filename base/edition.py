_viewer: bool = False


def is_viewer() -> bool:
    return _viewer


def set_viewer(value: bool = True) -> None:
    global _viewer
    _viewer = value
