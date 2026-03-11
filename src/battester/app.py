"""FastAPI web application for BatTester."""

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .models import BatteryChemistry, BatterySpec, TestState
from .tester import BatteryTester


BASE_DIR = Path(__file__).parent.parent.parent
tester = BatteryTester()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if tester.current_test and tester._running:
        await tester.stop_test()


app = FastAPI(
    title="BatTester",
    description="Battery Testing and Monitoring System",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class CreateTestRequest(BaseModel):
    name: str
    chemistry: BatteryChemistry = BatteryChemistry.LIION
    nominal_voltage: float = 3.7
    capacity_mah: int = 2000
    cell_count: int = 1


class StartTestRequest(BaseModel):
    discharge_rate_c: float = 0.5


class TestResponse(BaseModel):
    id: str
    name: str
    state: TestState
    voltage: Optional[float] = None
    current_ma: Optional[float] = None
    temperature_c: Optional[float] = None
    capacity_mah: float = 0.0
    energy_mwh: float = 0.0
    duration_seconds: float = 0.0
    reading_count: int = 0


def test_to_response(test) -> TestResponse:
    reading = test.latest_reading
    return TestResponse(
        id=test.id,
        name=test.name,
        state=test.state,
        voltage=reading.voltage if reading else None,
        current_ma=reading.current_ma if reading else None,
        temperature_c=reading.temperature_c if reading else None,
        capacity_mah=test.measured_capacity_mah,
        energy_mwh=reading.energy_mwh if reading else 0.0,
        duration_seconds=test.duration_seconds,
        reading_count=len(test.readings),
    )


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_test": tester.current_test.id if tester.current_test else None,
    }


@app.get("/api/tests")
async def list_tests() -> list[TestResponse]:
    return [test_to_response(t) for t in tester.list_tests()]


@app.post("/api/tests")
async def create_test(req: CreateTestRequest) -> TestResponse:
    spec = BatterySpec(
        chemistry=req.chemistry,
        nominal_voltage=req.nominal_voltage,
        capacity_mah=req.capacity_mah,
        cell_count=req.cell_count,
    )
    test = tester.create_test(req.name, spec)
    return test_to_response(test)


@app.get("/api/tests/{test_id}")
async def get_test(test_id: str) -> TestResponse:
    test = tester.get_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test_to_response(test)


@app.post("/api/tests/{test_id}/start")
async def start_test(test_id: str, req: StartTestRequest) -> TestResponse:
    success = await tester.start_discharge_test(test_id, req.discharge_rate_c)
    if not success:
        raise HTTPException(status_code=400, detail="Could not start test")
    test = tester.get_test(test_id)
    return test_to_response(test)


@app.post("/api/tests/{test_id}/stop")
async def stop_test(test_id: str) -> TestResponse:
    test = tester.get_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    await tester.stop_test()
    return test_to_response(test)


@app.get("/api/tests/{test_id}/readings")
async def get_readings(test_id: str, limit: int = 100):
    test = tester.get_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    readings = test.readings[-limit:] if limit else test.readings
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "voltage": r.voltage,
            "current_ma": r.current_ma,
            "temperature_c": r.temperature_c,
            "capacity_mah": r.capacity_mah,
            "energy_mwh": r.energy_mwh,
        }
        for r in readings
    ]
