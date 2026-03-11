# BatTester 🔋

Battery testing and monitoring system with real-time discharge capacity measurement, voltage/current graphing, and test history tracking.

## Features

- **Discharge Capacity Testing** - Measure actual battery capacity in mAh
- **Real-time Monitoring** - Live voltage, current, temperature readings
- **Interactive Dashboard** - Web UI with Chart.js visualizations
- **Test History** - Track and compare multiple battery tests
- **Simulation Mode** - Test the interface without hardware connected

## Quick Start

```bash
cd BatTester
./start.sh
```

The dashboard will be available at http://localhost:8090

## Project Structure

```
BatTester/
├── src/battester/
│   ├── __init__.py     # Package init
│   ├── models.py       # Data models (BatterySpec, BatteryReading, BatteryTest)
│   ├── tester.py       # Core testing logic
│   └── app.py          # FastAPI web application
├── static/
│   ├── style.css       # Dashboard styles
│   └── app.js          # Frontend JavaScript
├── templates/
│   └── dashboard.html  # Main dashboard template
├── tests/              # Test files
├── app.json            # Hub discovery manifest
├── requirements.txt    # Python dependencies
└── start.sh            # Startup script
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard UI |
| GET | `/api/health` | Health check |
| GET | `/api/tests` | List all tests |
| POST | `/api/tests` | Create new test |
| GET | `/api/tests/{id}` | Get test details |
| POST | `/api/tests/{id}/start` | Start discharge test |
| POST | `/api/tests/{id}/stop` | Stop running test |
| GET | `/api/tests/{id}/readings` | Get test readings |

## Hardware Integration

Currently runs in simulation mode. To connect real hardware:

1. Implement `read_hardware()` in `tester.py`
2. Add serial port configuration
3. Map voltage/current ADC readings to actual values

Supported interfaces (planned):
- Serial/USB (Arduino, ESP32)
- GPIO (Raspberry Pi)
- SCPI instruments

## Development

```bash
# Create venv and install deps
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with auto-reload
uvicorn src.battester.app:app --reload --port 8090
```

## License

MIT
