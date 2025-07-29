from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Optional
from datetime import datetime, timezone


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


@dataclass
class Order:
    order_id: str
    cargo_bind_id: str
    customer_name: str
    delivery_address: str
    delivery_lat: float
    delivery_lng: float
    quantity: int
    status: str
    assigned_robot_id: str
    created_at: str = field(
        default_factory=lambda: datetime
        .now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

@dataclass
class OrderInfo:
    order_id: str
    auth_code: str
    expires_at: str
    message: str
    complete_flag: bool

    
@dataclass
class Orders:
    orders: List[Order] = field(default_factory=list)
    orders_info: List[OrderInfo] = field(default_factory=list)
