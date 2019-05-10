import inspect
import json
from typing import NamedTuple


def to_dict(src) -> dict:
    if isinstance(src, tuple):
        return {
                k: to_dict(v)
                for k, v in inspect.getmembers(src)
                if not callable(v) and not k.startswith('_')
                }
    elif isinstance(src, dict):
        return {
                k: to_dict(v)
                for k, v in src.items()
                }
    elif isinstance(src, list):
        return [ to_dict(v) for v in src ]
    else:
        return src

def indent_json(src: bytes)->bytes:
    j = json.loads(src)
    return json.dumps(j, indent=2).encode('utf-8')

if __name__ == '__main__':

    class Hoge(NamedTuple):
        name: str

    class Fuga(NamedTuple):
        hoge: Hoge

    t = Fuga(Hoge('hoge'))
    print(to_dict(t))
