# RPi Car Infotainment

A car infotainment system designed to run on a Raspberry Pi.

## Dependencies

### Core Dependencies
- Python 3.11+
- PyQt6
- obd
- requests

### Optional Dependencies
- pygame (for music player functionality)

## Installation

1. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pyqt6
   ```

2. Install Python dependencies:
   ```bash
   pip install obd requests
   ```

3. For music player functionality (optional):
   ```bash
   pip install pygame
   ```

## Running the Application

### Normal Mode (with GUI)
```bash
python main.py
```

### Headless Mode (for testing)
```bash
python run_headless.py
```

## Troubleshooting

### Music Player
The music player functionality uses pygame for audio playback. Music files are stored in the `music/library` folder within the project directory. The player includes a download feature with a progress bar to show download status. If you encounter any issues with audio playback, make sure pygame is installed correctly.

### Display Issues
If you're getting errors related to the display or XCB, make sure you're running the application in a graphical environment. Alternatively, use the headless mode for testing.

### OBD Connection Issues
Make sure the OBD adapter is properly connected and the port is correctly configured in the settings.

## Configuration

The application uses a `config.json` file for configuration. If the file doesn't exist, it will be created with default values.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
