import sys
import os

# Add hostel_allocation_system to sys.path so imports work seamlessly
app_dir = os.path.join(os.path.dirname(__file__), "hostel_allocation_system")
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from hostel_allocation_system.run import app

if __name__ == "__main__":
    app.run(debug=True)
