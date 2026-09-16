#!/usr/bin/env python3
#
# repos.yml parsing, shared by bin/repos and anything else that needs the
# manifest. Accepts a deliberate subset of YAML — a `workspace:` mapping and a
# `repos:` list of flat string mappings — so the workspace has no PyYAML
# dependency and a malformed file fails with a line number.

FIELDS = ("dir", "url", "trunk", "stack", "setup")
REQUIRED = ("dir", "url")


class RepoFileError(Exception):
    pass


def strip_comment(raw):
    out, quote = [], None
    for char in raw:
        if quote:
            out.append(char)
            quote = None if char == quote else quote
        elif char in "\"'":
            quote = char
            out.append(char)
        elif char == "#":
            break
        else:
            out.append(char)
    return "".join(out).rstrip()


def _pair(body, lineno, allowed):
    key, sep, value = body.partition(":")
    if not sep:
        raise RepoFileError(f"line {lineno}: expected `key: value`, got `{body}`")
    key, value = key.strip(), value.strip()
    if key not in allowed:
        raise RepoFileError(f"line {lineno}: unknown key `{key}` (expected: {', '.join(allowed)})")
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return key, value


def parse(path, allow_empty=False):
    if not path.is_file():
        raise RepoFileError(f"{path} does not exist")
    workspace, repos, current, section = {}, [], None, None

    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = strip_comment(raw)
        if not line.strip():
            continue
        if not line[0].isspace():
            section = {"workspace:": "workspace", "repos:": "repos"}.get(line.rstrip())
            if section is None:
                raise RepoFileError(f"line {lineno}: expected `workspace:` or `repos:`, got `{line}`")
            current = None
            continue
        if section is None:
            raise RepoFileError(f"line {lineno}: indented content before any section key")

        body = line.strip()
        if section == "workspace":
            key, value = _pair(body, lineno, ("git_base",))
            workspace[key] = value
            continue
        if body.startswith("- "):
            current = {}
            repos.append(current)
            body = body[2:].strip()
            if not body:
                continue
        elif current is None:
            raise RepoFileError(f"line {lineno}: `{body}` is not inside a `- dir: …` entry")
        key, value = _pair(body, lineno, FIELDS)
        if key in current:
            raise RepoFileError(f"line {lineno}: `{key}` set twice in the same entry")
        current[key] = value

    _check(repos, allow_empty)
    return workspace, repos


def _check(repos, allow_empty):
    if not repos and not allow_empty:
        raise RepoFileError("`repos:` is empty — add one with `./bin/repos add <clone-url>`")
    seen = set()
    for index, repo in enumerate(repos, 1):
        for field in REQUIRED:
            if not repo.get(field):
                raise RepoFileError(f"entry {index}: `{field}` is required")
        directory = repo["dir"]
        if "/" in directory or directory.startswith("."):
            raise RepoFileError(f"entry {index}: dir `{directory}` must be a plain child directory name")
        if directory in seen:
            raise RepoFileError(f"entry {index}: dir `{directory}` is declared twice")
        seen.add(directory)
        repo.setdefault("trunk", "main")
        for field in FIELDS:
            repo.setdefault(field, "")
