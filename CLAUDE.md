# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python desktop application called "DJs Timeline-maskin" (DJs Timeline Machine). It is designed to help investigative journalists and researchers to quickly renaming pdf files and/or create timelines i excel. The first part of the app processes PDF files extracts different parts of the filename. User can then edit these parts and rename the file. It is also possible to copy the old or new file name to the second part of the app: The excel integration. Here the user can add information to a number of fields. By cklicking a button user can then both rename the pdf-file and add a row to a selected excel-document. 
A third way to use the app is by manually add content to excel-fields and create a new excel row without any pdf file selected or renamed. This is practical for researchers whon for example is picking information from books or other sources. 
The application has been refactored from a single large file into a modular structure.

## Additional guideline on github commit
**Never* mention yourself (Claude) in comment when doing commit. *Never* write stuff like "🤖 Generated with [Claude Code](https://claude.ai/code) Co-Authored-By: Claude <noreply@anthropic.com>". 

## Running the Application

```bash
python app.py
```

## Dependencies

The application requires these Python packages:
- `ttkbootstrap` - Modern tkinter styling
- `PyPDF2` - PDF processing
- `openpyxl` - Excel file manipulation

Install dependencies:
```bash
pip install ttkbootstrap PyPDF2 openpyxl xlsxwriter
```

## Architecture

The application is structured with the following modular organization:

```
├── app.py                    # Main entry point
├── core/
│   ├── __init__.py
│   ├── config.py            # ConfigManager class
│   ├── pdf_processor.py     # PDFProcessor class
│   ├── filename_parser.py   # FilenameParser class
│   └── excel_manager.py     # ExcelManager class
├── gui/
│   ├── __init__.py
│   ├── main_window.py       # PDFProcessorApp class (main GUI)
│   ├── dialogs.py           # DialogManager class
│   ├── excel_fields.py      # ExcelFieldManager class
│   └── utils.py             # ToolTip and other GUI utilities
└── utils/
    ├── __init__.py
    └── constants.py         # VERSION, CONFIG_FILE constants
```

### Core Classes

- **PDFProcessorApp** (gui/main_window.py): Main GUI application class - handles all GUI layout and user interaction
- **DialogManager** (gui/dialogs.py): Dialog management and user interactions
- **ExcelFieldManager** (gui/excel_fields.py): Excel field creation and layout management
- **PDFProcessor** (core/pdf_processor.py): PDF file operations and validation
- **FilenameParser** (core/filename_parser.py): Filename parsing and text cleaning
- **ExcelManager** (core/excel_manager.py): Excel file operations and formatting
- **ConfigManager** (core/config.py): Application configuration persistence
- **ToolTip, ScrollableText, ScrollableFrame** (gui/utils.py): GUI utilities including tooltips, scrollable text widgets, and full-window scrolling

## Key Features

1. **PDF Processing**: Extract text from PDF files using PyPDF2
2. **Filename Generation**: Parse PDF content to generate structured filenames
3. **Excel Integration**: Update Excel spreadsheets with extracted information
4. **Configuration Management**: Save/load user preferences and settings
5. **Modern GUI**: Built with ttkbootstrap for modern appearance

## Configuration

The application uses JSON configuration stored in `pdf_processor_config.json` with:
- **Excel file path** - Path to selected Excel file
- **Last PDF directory** - Last used PDF directory for file dialog
- **Window geometry** - Window size and position
- **Theme settings** - ttkbootstrap theme selection
- **Locked field configurations** - Which fields are locked (true/false)
- **Locked field contents** - Plain text content of locked fields
- **Locked field formats** *(v1.14.0)* - Rich text formatting data for locked fields

### Configuration Structure (v1.14.0)
```json
{
  "excel_file": "path/to/excel/file.xlsx",
  "window_geometry": "2560x1320+-112+21",
  "theme": "simplex",
  "locked_fields": {
    "Note1": true,
    "Händelse": false
  },
  "locked_field_contents": {
    "Note1": "Plain text content"
  },
  "locked_field_formats": {
    "Note1": [
      {
        "tag": "bold",
        "start": "1.0", 
        "end": "1.15"
      }
    ]
  }
}
```

**Backward Compatibility**: Configuration files from previous versions work seamlessly. Missing `locked_field_formats` section is treated as empty formatting.

## Excel hybrid methods
v1.7.4 contains the COMPLETE WORKING Excel hybrid method. 
These methods solved persistant problems that the app had with writing corrextly formatted text to excel cells. 
The breakthrough hybrid approach consista of:
- openpyxl for reading existing Excel data (preserves formulas)  
- xlsxwriter for writing new data (handles rich text perfectly)
- Method 2 character-by-character algorithm for text extraction
This method might seem complicated but is important to understand that this is the only way we've found to make the app to write perfect Excel rich text formatting with colors, bold, italic, line breaks.

## Current Status (v1.18.2)

**COMPLETED ✅ - STABLE VERSION RESTORED**: Reset to v1.18.2 after discovering critical config saving issues in later versions

### Working Features (v1.18.2):
- ✅ **Theme-Independent Color Buttons**: Formatting toolbar colors remain fixed across all themes ✅ NEW!
- ✅ **Clean Formatting System**: Bold + 3 colors only - guaranteed Excel compatibility
- ✅ **Excel Hybrid Method Protected**: No risk to reliable Excel export functionality
- ✅ **Simplified User Interface**: Bold, Red, Green, Blue, T-clear, A+ font buttons only
- ✅ **Perfect Excel Export**: All formatting combinations export flawlessly to Excel
- ✅ **Strict Validation System**: Both Startdatum and Händelse must be filled for Excel row creation
- ✅ **PDF-Only Operations**: PDF renaming works without Excel validation when both required fields are empty
- ✅ **Enhanced Error Messages**: Clear guidance for users on field requirements with PDF-only hint
- ✅ **Correct 'Nothing to Do' Logic**: Proper message when no operations are needed
- ✅ **Rich Text Background Colors**: All text fields support background colors correctly
- ✅ **Output Folder Selection**: Flexible destination for renamed PDFs with session-only lock and folder opening
- ✅ **Font Size Toggle**: A+ button in text fields for cycling through 9pt → 12pt → 15pt with proper bold formatting
- ✅ **Scrollable Text Widgets**: All text fields (Händelse, Note1-3) now have vertical scrollbars
- ✅ **Excel File Persistence**: App remembers selected Excel file between sessions
- ✅ **Full-Window Scrollbar**: Canvas-based scrolling for low-resolution screen support
- ✅ **Code Quality**: All major code issues resolved, clean Ruff validation
- ✅ **Date/Time Validation**: Comprehensive validation system with multiple trigger events
- ✅ **Rich Text Persistence**: Bold and color formatting preserved across app sessions
- ✅ **Time Fields**: Starttid and Sluttid with HH:MM validation and auto-formatting
- ✅ **19 Excel Columns**: All original fields plus new time fields
- ✅ **Core Functionality**: PDF processing, Excel integration, locked fields all working
- ✅ **Professional Toolbar**: Clean formatting toolbar with intuitive design and color-coded buttons
- ✅ **T Button Clear Formatting**: T button removes ALL formatting and restores text widget's default color
- ✅ **Error Handling**: Professional retry/cancel dialogs for file lock scenarios

### Completed Major Fixes (v1.17.13-v1.17.17):
- ✅ **Strict Validation Implementation (v1.17.17)**: Complete overhaul of save operation logic with proper Startdatum/Händelse validation
- ✅ **PDF-Only Operation Support (v1.17.17)**: Fixed logic to allow PDF renaming without Excel field validation
- ✅ **Rich Text Background Colors**: Successfully resolved with correct xlsxwriter API usage and color preservation system
- ✅ **T Button Clear Formatting**: Fixed to remove ALL formatting and use text widget's actual default color instead of theme system color
- ✅ **Uniform Formatting Excel Export**: Fixed xlsxwriter edge case where uniformly formatted text disappeared in Excel

### Rich Text Format Preservation (v1.18.0)
**CLEAN SYSTEM**: Format preservation for locked text fields with simplified formatting options

**Text Fields with Format Preservation**: Note1, Note2, Note3, Händelse
**Supported Formatting**: Bold, Colors (Red, Blue, Green, Default)
**Format Storage**: JSON-compatible tag ranges in configuration file
**Usage**: Apply formatting → Lock field → Formatting preserved across sessions
**Excel Compatibility**: 100% guaranteed with all supported formatting combinations

## Known Issues

### Rich Text Background Colors (v1.17.9-v1.17.14) - COMPLETED ✅
- **Status**: All text fields including rich text now support background colors ✅ FIXED!
- **Root Cause**: `xlsxwriter.write_rich_string()` required format parameter + existing rows lost color detection
- **Investigation**: Two-phase fix - correct API usage (v1.17.13) + color preservation (v1.17.14)
- **Final Solution**: Correct xlsxwriter API + `_extract_row_color_from_format()` method for existing rows
- **Result**: Perfect background color support across all field types with full formatting preservation

### Rich Text Uniform Formatting Bug (Excel Export) - COMPLETED ✅
- **Status**: All text fields including uniform formatting now work correctly in Excel ✅ FIXED!
- **Root Cause**: `xlsxwriter.write_rich_string()` designed for mixed formatting, failed with uniform patterns  
- **Investigation**: Identified edge case where `[format_obj, "entire text"]` pattern caused text to disappear
- **Final Solution**: Smart detection + fallback to `worksheet.write()` for uniform formatting cases
- **Result**: Perfect Excel export for both uniform and mixed formatting with preserved functionality

### Window Height on External Monitors
- ✅ **Laptop screens**: Full functionality, all elements visible
- ⚠️ **External monitors**: Slightly shortened window (800px max) but fully functional
- **Impact**: Minimal - all features accessible, status bar visible

## Modular Refactoring - COMPLETED ✅

### Phase 1: Dialog Extraction (v1.9.3) - ✅ COMPLETED
- Created `gui/dialogs.py` with `DialogManager` class
- Extracted 4 dialog methods (~540 lines from main_window.py)
- Application tested and working perfectly

### Phase 2: Excel Field Management (v1.9.5) - ✅ COMPLETED  
- Created `gui/excel_fields.py` with `ExcelFieldManager` class
- Extracted 6 Excel field methods (~400-500 lines from main_window.py)
- Perfect 3-column layout preserved with all functionality

## Important Development Rules
- **Never edit** `APP DJs Timeline-verktyg v170 FUNKAR.py` - old single-file version (backup)
- **Always use** `app.py` as the starting point for the refactored modular version
- **Never** try to change the Excel hybrid methods without asking the user - v1.7.4 contains the only working solution
- **Preserve working code**: When refactoring, extract code exactly as-is, don't "improve" during extraction
- **Test immediately**: After any structural changes, test the application thoroughly
- **Grid layout is sacred**: The three-column Excel fields layout uses grid with `uniform="col"` - never change this

## Development Notes

- All GUI components are built using ttkbootstrap
- Logging is configured for debugging
- No automated tests are present in the codebase
- No build process required - runs directly with Python interpreter
- **Current version**: v1.18.2 (stable master with working config saving - reset after v1.18.3/v1.18.4 issues)
- **Last tested**: 2025-07-30 - Config saving verified working perfectly, locked fields and rich text preserved

For detailed version history and development milestones, see DEVELOPMENT_HISTORY.md