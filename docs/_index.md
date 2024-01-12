---
title: "Introduction"
draft: false
type: docs
layout: "single"

menu:
  docs_extensions:
      weight: 0
---
# Introduction
The `exchange-calendars-extensions` Python package transparently adds some features to the `exchange-calendars` package. 
It can be used without any changes to existing code that already uses [`exchange-calendars`](https://example.com).

## System requirements
The package requires Python 3.8 or later.

## Installation
The package is available on [PyPI](https://pypi.org/project/exchange-calendars-extensions/) and can be installed via 
[pip](https://pip.pypa.io/en/stable/) or any other suitable package/dependency management tool, e.g. 
[Poetry](https://python-poetry.org/).

{{< tabs tabTotal="2" tabID1="installing-with-pip" tabID2="installing-with-poetry" tabName1="With pip" tabName2="With Poetry">}}

{{< tab tabID="installing-with-pip" >}}

{{< steps >}}
{{< step >}}
**Install**

```bash
pip install exchange-calendars-extensions
```
{{< /step >}}
{{< step >}}
**Install (advanced)**

You can pin to a specific package version. For example, to install version 1.0:

```bash
pip install exchange-calendars-extensions==1.0
```
{{< /step >}}
{{< step >}}
**Uninstall**

```bash
pip uninstall exchange-calendars-extensions
```
{{< /step >}}
{{< /steps >}}

{{< /tab >}}
{{< tab tabID="installing-with-poetry" >}}
To add the package to a project managed with Poetry, add it to the project's `pyproject.toml` file:

```toml
[tool.poetry.dependencies]
exchange-calendars-extensions = "^1.0"
```

Then, run `poetry install` to install the package.

{{< /tab >}}
{{< /tabs >}}
