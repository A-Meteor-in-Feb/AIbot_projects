from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Item:
    name: str
    quantity: int
    weight: float
    category: Optional[str] = None

    @property
    def total_weight(self) -> float:
        
        return self.weight * self.quantity


@dataclass
class CargoBin:
    bin_id: int
    capacity: float
    items: List[Item] = field(default_factory=list)

    @property
    def total_weight(self) -> float:
        
        return sum(item.total_weight for item in self.items)

    @property
    def utilization(self) -> float:
        
        if self.capacity <= 0:
            return 0.0
        return self.total_weight / self.capacity


@dataclass
class Inventory:
    bins: List[CargoBin] = field(default_factory=list)

    @property
    def total_capacity(self) -> float:
        
        return sum(bin.capacity for bin in self.bins)

    @property
    def total_weight(self) -> float:
        
        return sum(bin.total_weight for bin in self.bins)

    @property
    def total_utilization(self) -> float:
        
        cap = self.total_capacity
        return (self.total_weight / cap) if cap > 0 else 0.0
