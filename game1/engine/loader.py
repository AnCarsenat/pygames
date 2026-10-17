import importlib.util
import sys
import traceback
from pathlib import Path

from .minigame import MiniGame


def load_games(directory):
    games = []
    for path in sorted(Path(directory).glob("*.py")):
        if path.name.startswith("_"):
            continue
        module = _import_file(path)
        if module:
            games.extend(_game_classes(module, path.stem))
    return games


def _import_file(path):
    name = f"minigames_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        del sys.modules[name]
        print(f"Skipping {path.name}:", file=sys.stderr)
        traceback.print_exc()
        return None
    return module


def _game_classes(module, slug):
    found = []
    for value in vars(module).values():
        if (
            isinstance(value, type)
            and issubclass(value, MiniGame)
            and value is not MiniGame
            and value.__module__ == module.__name__
            and not value.__name__.startswith("_")
        ):
            value.slug = slug
            found.append(value)
    return found
