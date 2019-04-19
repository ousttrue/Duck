# Duck
A simple tool like make using TOML 🦆

## sample

Duck.toml

```toml
@default = "hello"

# entries
[duck]
command = ["echo", "🐣🐣🐣"]

[hello]
depends = ["duck"]
command = ["echo", "hello 🦆"]
```

```
$ duck
🐣🐣🐣
hello 🦆
```

