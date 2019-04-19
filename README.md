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

```toml
@default = "build"

[generate]
cwd = "build"
command = ["cmake", ".."]

[build]
depends = ["generate"]
cwd = "build"
command = ["make"]
```

