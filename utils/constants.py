"""
Constants and configuration values for the DJ Timeline application
"""

# Configuration
CONFIG_FILE = "djs_timeline_machine_config.json"
VERSION = "v2.2.7"

# Required Excel columns - these must exist in the Excel file
REQUIRED_EXCEL_COLUMNS = [
    'OBS', 'Inlagd', 'Kategori', 'Underkategori',
    'Person/sak', 'Special', 'Händelse', 'Dag',
    'Startdatum', 'Starttid', 'Slutdatum', 'Sluttid', 'Note1', 'Note2', 'Note3',
    'Källa1', 'Källa2', 'Källa3', 'Övrigt'
]
