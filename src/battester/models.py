"""Battery data models and types."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class BatteryChemistry(str, Enum):
    LIION = "li-ion"
    LIPO = "lipo"
    NIMH = "nimh"
    LEAD_ACID = "lead-acid"
    LIFEPO4 = "lifepo4"
    UNKNOWN = "unknown"


class TestState(str, Enum):
    IDLE = "idle"
    CHARGING = "charging"
    DISCHARGING = "discharging"
    RESTING = "resting"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class BatterySpec:
    """Specifications for a battery under test."""
    chemistry: BatteryChemistry = BatteryChemistry.UNKNOWN
    nominal_voltage: float = 3.7
    capacity_mah: int = 0
    cell_count: int = 1
    max_charge_rate_c: float = 1.0
    max_discharge_rate_c: float = 1.0


@dataclass
class BatteryReading:
    """A single measurement from the battery tester."""
    timestamp: datetime
    voltage: float
    current_ma: float
    temperature_c: Optional[float] = None
    capacity_mah: float = 0.0
    energy_mwh: float = 0.0
    state: TestState = TestState.IDLE


@dataclass
class BatteryTest:
    """A complete battery test session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Unnamed Test"
    spec: BatterySpec = field(default_factory=BatterySpec)
    readings: list[BatteryReading] = field(default_factory=list)
    state: TestState = TestState.IDLE
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        if not self.started_at:
            return 0.0
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds()
    
    @property
    def measured_capacity_mah(self) -> float:
        if not self.readings:
            return 0.0
        return max(r.capacity_mah for r in self.readings)
    
    @property
    def latest_reading(self) -> Optional[BatteryReading]:
        return self.readings[-1] if self.readings else None
