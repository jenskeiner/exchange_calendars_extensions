# Exchange Calendar Service

A library based on [exchange_calendars](https://github.com/gerrymanoim/exchange_calendars) that adds additional
features to the calendars:

- Combined calendars for regular and ad-hoc holidays/special open days/special close days.
- Calendars for the last trading session of each month, and the last *regular* trading session of each month.
- Calendars with weekend days.
- The ability to modify existing calendars by adding or removing special days programmatically at runtime.
- Select exchanges: Calendars for monthly and quarterly expiry days (aka quadruple witching).

## Build/Run

```bash
uv build
```

To use the library, it needs to be imported from Python code; see [README.md](./README.md) for examples.

## Documentation

Documentation is kept in README.md for GitHub and in several Markdown files in docs/ from where
[Zensical](https://zensical.org/) generates a static documentation site.

When you have finished a task, always ensure that the user facing documentation is updated and in line with the public
API.

### Zensical

The main entry point in docs/ is `index.md`, further sections and subsections are in separate files and subdirectories.
A quick reference how Zensical supports Markdown is in [markdown.md](./support/markdown.md).

## Conventions

- Python 3.12+, type hints required everywhere
- When making changes:
    - make code changes
    - run all tests
    - fix issues iteratively until all pass
    - update any related documentation, i.e. this file and README.md, where necessary.
- Comments only for non-obvious logic
- Pydantic for config/data classes
- `gh` CLI for GitHub auth (no separate token)
- Avoid using @dataclass, use Pydantic instead
- Test are grouped into files matching the directory structure of the code under test.
- Test classes group tests that are related to the same functionality.
- Prefer immutable collections (e.g. tuples) over mutable ones (e.g. lists) where possible.

## Testing

```bash
uv run pytest -v tests/ --cov=exchange_calendar_service --cov-fail-under=80
```

Coverage gate: 80% minimum.
