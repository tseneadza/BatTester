"""Battery tester core logic."""

import asyncio
import random
from datetime import datetime
from typing import Callable, Optional

from .models import BatteryTest, BatteryReading, BatterySpec, TestState


class BatteryTester:
    """Core battery testing controller.
    
    Currently implements simulation mode. Hardware interfaces can be added
    by implementing the `read_hardware()` method or connecting via serial.
    """
    
    def __init__(self):
        self.current_test: Optional[BatteryTest] = None
        self.tests: dict[str, BatteryTest] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._on_reading: Optional[Callable[[BatteryReading], None]] = None
    
    def create_test(self, name: str, spec: BatterySpec) -> BatteryTest:
        """Create a new battery test."""
        test = BatteryTest(name=name, spec=spec)
        self.tests[test.id] = test
        return test
    
    async def start_discharge_test(self, test_id: str, 
                                    discharge_rate_c: float = 0.5) -> bool:
        """Start a discharge capacity test."""
        if test_id not in self.tests:
            return False
        
        self.current_test = self.tests[test_id]
        self.current_test.state = TestState.DISCHARGING
        self.current_test.started_at = datetime.now()
        self._running = True
        
        self._task = asyncio.create_task(
            self._run_discharge_simulation(discharge_rate_c)
        )
        return True
    
    async def stop_test(self) -> bool:
        """Stop the current test."""
        if not self._running or not self.current_test:
            return False
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        self.current_test.state = TestState.COMPLETE
        self.current_test.completed_at = datetime.now()
        return True
    
    async def _run_discharge_simulation(self, discharge_rate_c: float):
        """Simulate a discharge test with realistic battery behavior."""
        if not self.current_test:
            return
        
        spec = self.current_test.spec
        voltage = spec.nominal_voltage * spec.cell_count * 1.15
        min_voltage = spec.nominal_voltage * spec.cell_count * 0.8
        current_ma = spec.capacity_mah * discharge_rate_c
        capacity_mah = 0.0
        energy_mwh = 0.0
        
        interval_s = 1.0
        
        while self._running and voltage > min_voltage:
            noise = random.uniform(-0.02, 0.02)
            voltage_drop = (spec.nominal_voltage * 0.001) + noise
            voltage = max(min_voltage, voltage - voltage_drop)
            
            delta_capacity = current_ma * (interval_s / 3600)
            capacity_mah += delta_capacity
            energy_mwh += delta_capacity * voltage
            
            reading = BatteryReading(
                timestamp=datetime.now(),
                voltage=round(voltage, 3),
                current_ma=round(current_ma + random.uniform(-5, 5), 1),
                temperature_c=round(25 + random.uniform(-1, 3), 1),
                capacity_mah=round(capacity_mah, 1),
                energy_mwh=round(energy_mwh, 1),
                state=TestState.DISCHARGING,
            )
            
            self.current_test.readings.append(reading)
            
            if self._on_reading:
                self._on_reading(reading)
            
            await asyncio.sleep(interval_s)
        
        if self._running:
            self.current_test.state = TestState.COMPLETE
            self.current_test.completed_at = datetime.now()
            self._running = False
    
    def get_test(self, test_id: str) -> Optional[BatteryTest]:
        return self.tests.get(test_id)
    
    def list_tests(self) -> list[BatteryTest]:
        return list(self.tests.values())
    
    def on_reading(self, callback: Callable[[BatteryReading], None]):
        """Register a callback for new readings."""
        self._on_reading = callback
