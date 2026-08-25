"""Tests for the example module — delete or replace with your own tests."""

from bqutil.example import Greeter


def test_greeter():
    g = Greeter(name="World")
    assert g.greet() == "Hello, World!"


def test_greeter_custom_name():
    g = Greeter(name="Agent")
    assert g.greet() == "Hello, Agent!"
