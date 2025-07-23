#!/usr/bin/env python3
"""
DJs Timeline-maskin
- Process single PDF file and rename based on content
- Update Excel file with information
- Simplified single-file workflow
"""

import logging

from gui.main_window import PDFProcessorApp
from utils.constants import VERSION

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_dependencies() -> bool:
    """Check if all required packages are installed"""
    missing_packages = []

    try:
        import ttkbootstrap
    except ImportError:
        missing_packages.append("ttkbootstrap")

    try:
        import PyPDF2
    except ImportError:
        missing_packages.append("PyPDF2")

    try:
        import openpyxl
    except ImportError:
        missing_packages.append("openpyxl")

    try:
        import xlsxwriter
    except ImportError:
        missing_packages.append("xlsxwriter")

    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  pip install {package}")
        return False

    return True


def main():
    """Main entry point"""
    print(f"DJs Timeline-maskin {VERSION}")
    print("=" * 50)

    if not check_dependencies():
        print("\nInstall missing packages before running the application.")
        return

    print("All required packages are installed")
    print("Starting application...")

    try:
        app = PDFProcessorApp()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
