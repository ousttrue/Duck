# Duck
A simple tool like make using TOML 🦆

## sample

Duck.toml

```toml
# entries
[duck]
command = ["echo", "🐣🐣🐣"]

[hello]
depends = ["duck"]
command = ["echo", "hello 🦆"]
```

```
$ duck hello
🐣🐣🐣
hello 🦆
```

## cmake

```toml
[generate]
cwd = "build"
command = ["cmake", ".."]

[build]
depends = ["generate"]
cwd = "build"
command = ["make"]
```

