from dataclasses import dataclass
from dataclasses import field
from typing import List

@dataclass
class Robot:
    robotId: str
    robotIP: str

@dataclass
class Robots:
    robots: List[Robot] = field(default_factory=list)