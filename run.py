import os
import sys

# Add hostel_allocation_system directory to sys.path so 'app' package is found directly
sub_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hostel_allocation_system")
if sub_dir not in sys.path:
    sys.path.insert(0, sub_dir)

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
