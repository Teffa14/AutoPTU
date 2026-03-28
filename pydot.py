"""Minimal pydot compatibility stub for local py_trees usage.

This project only uses py_trees' text/unicode display helpers. The upstream
package imports pydot unconditionally for DOT export support, so provide a very
small fallback surface here instead of adding a full graphviz dependency.
"""

from __future__ import annotations


class _Base:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.children = []

    def add_node(self, node):
        self.children.append(node)

    def add_edge(self, edge):
        self.children.append(edge)

    def add_subgraph(self, graph):
        self.children.append(graph)

    def set_name(self, *_args, **_kwargs):
        return None

    def set_label(self, *_args, **_kwargs):
        return None

    def set(self, *_args, **_kwargs):
        return None

    def to_string(self):
        return "digraph G {}"


class Dot(_Base):
    pass


class Node(_Base):
    pass


class Edge(_Base):
    pass


class Subgraph(_Base):
    pass

