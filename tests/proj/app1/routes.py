import typing as t

from unfazed.route import Route, path

from .endpoints import add_endpoint

patterns: t.List[Route] = [path("/add", endpoint=add_endpoint)]
