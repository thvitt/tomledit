# TOMLEdit (te): Tiny CLI TOML Manipulator

TOMLEdit is a small command line tool to manipulate individual keys in a TOML file without starting an editor. If nothing else is specified, it works on pyproject.toml in the current or a parent directory.

The idea is that you pass alternating keys and values to te, and it will probably do what you want:

pyproject.toml before:

```toml
[project]
name = "tomledit"
version = "0.1.0"
authors = [{ name = "Thorsten Vitt", email = "thorsten.vitt@uni-wuerzburg.de" }]
requires-python = ">=3.13"
dependencies = ["cyclopts>=3.16.2", "tomlkit>=0.13.2"]
```

Command:

```bash
te project.version 0.2.0 project.readme README.md project.authors '{name = "John Doe", email = "john.doe@example.org"}'
```

pyproject.toml after:

```toml
[project]
name = "tomledit"
version = "0.2.0"
readme = "README.md"
authors = [{ name = "Thorsten Vitt", email = "thorsten.vitt@uni-wuerzburg.de" }, {name = "John Doe", email = "john.doe@example.org"}]
requires-python = ">=3.13"
dependencies = ["cyclopts>=3.16.2", "tomlkit>=0.13.2"]
```

You can also factor out the common prefix `project` from the command using the `-p` (or `--prefix`) option:

```bash
te -p project version 0.2.0 readme README.md authors '{name = "John Doe", email = "john.doe@example.org"}'
```

will have the same effect.

Use `-f filename.toml` to work on _filename.toml_ instead of the nearest _pyproject.toml_ that can be found. Use something like `-F pixi.toml`  to find the nearest _pixi.toml_ in the current or ancestor directory.

By default, _te_ will automatically add to a list if it finds a list at the given key (as with the _authors_ in the example above), and set or add the key in any other case. You can intersperse the key/value arguments with _mode switch_ characters `+`, `-`, `=`, `@` to modify this behaviour:

| switch | mode | arguments     | description |
|--------|------|---------------|-------------|
| @      | auto | key value ... | If the key points to a list, the value is appended. Otherwise, the entry at the key is set to the value, replacing any existing value. |
| =      | set  | key value ... | The entry at the key is set to the value, replacing any existing value. |
| +      | add  | key value ... | If the key points to a list, the value is appended. If the key does not exist, it is created as a list with the value. If the key exists and is not a list, it is converted to a list and the value is appended. |
| -      | remove| key ...       | The entries at the given keys are removed. If the key points to a list, the value is removed from the list. |

E.g., `te -p tool.ruff fix true + extend-include "*.pyw"` will set _fix_ to true. Additionally, if the _extend-include_ list exists, `"*.pyw"` will be added to it, otherwise a list will be created (due to the `+` mode)
