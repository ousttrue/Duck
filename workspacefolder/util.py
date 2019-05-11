import inspect
import json
from typing import NamedTuple, Any


def to_dict(src) -> Any:
    if isinstance(src, tuple):
        return {
            k: to_dict(v)
            for k, v in inspect.getmembers(src)
            if not callable(v) and not k.startswith('_')
        }
    elif isinstance(src, dict):
        return {k: to_dict(v) for k, v in src.items()}
    elif isinstance(src, list):
        return [to_dict(v) for v in src]
    else:
        return src


def indent_json(src: bytes) -> str:
    j = json.loads(src.decode('utf-8'))
    return json.dumps(j, indent=2)


if __name__ == '__main__':

    class Hoge(NamedTuple):
        name: str

    class Fuga(NamedTuple):
        hoge: Hoge

    t = Fuga(Hoge('hoge'))
    print(to_dict(t))
