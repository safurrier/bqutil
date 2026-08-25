"""Example module — delete or replace with your own code."""

from dataclasses import dataclass


@dataclass
class Greeter:
    """A simple greeter to demonstrate the project structure."""

    name: str

    def greet(self) -> str:
        return f"Hello, {self.name}!"
