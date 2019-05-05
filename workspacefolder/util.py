import inspect
from typing import NamedTuple


def to_dict(src) -> dict:
    if isinstance(src, tuple):
        return {
            k: to_dict(v)
            for k, v in inspect.getmembers(src)
            if not callable(v) and not k.startswith('_')
        }
    else:
        return src


if __name__ == '__main__':

    class Hoge(NamedTuple):
        name: str

    class Fuga(NamedTuple):
        hoge: Hoge

    t = Fuga(Hoge('hoge'))
    print(to_dict(t))
