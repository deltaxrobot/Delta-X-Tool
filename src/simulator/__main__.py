import sys
import os

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from PyQt5.QtWidgets import QApplication
from src.simulator.gui import MainWindow

def main():
    """Main entry point for the robot simulator."""
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 