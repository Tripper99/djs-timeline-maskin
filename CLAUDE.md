# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python desktop application called "DJs Timeline-maskin" (DJs Timeline Machine). It is designed to help investigative journalists and researchers to quickly renaming pdf files and/or create timelines i excel. The first part of the app processes PDF files extracts different parts of the filename. User can then edit these parts and rename the file. It is also possible to copy the old or new file name to the second part of the app: The excel integration. Here the user can add information to a number of fields. By cklicking a button user can then both rename the pdf-file and add a row to a selected excel-document. 
A third way to use the app is by manually add content to excel-fields and create a new excel row without any pdf file selected or renamed. This is practical for researchers whon for example is picking information from books or other sources. 
The application has been refactored from a single large file into a modular structure.

## General guidelines for Claude Code
-- Be direct; avoid ungrounded or sycophantic flattery. 
-- Be modest. Never clasim that a problem is solved before testruns.  
-- **Never start to write code without user saying that it is OK. 
-- **Always run test for syntax errors using Ruff before letting the user do test runs.
-- **Always update version number after changing the code. 
-- **Always assume that the user is using Windows.
-- If you want the user to do a test run of the code then don't start the app yourself. Tell the user to start it and explain what tests should be done.  
-- If problems persist suggest writing test scripts for analyzing problems in a systematic way.

## Git Commit Guidelines
-- Please do not mention yourself (Claude) as a co-author when committing, och include any links to Claude Code or any other sites. 
-- Always git add . and commit with a new version number before writing code. 
-- Add comments on the performance after testing the new version.

## Documentation Memories
-- Please use context7 to find relevant, up-to-date documentation for libraries etc. 

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
│   └── utils.py             # ToolTip and other GUI utilities
└── utils/
    ├── __init__.py
    └── constants.py         # VERSION, CONFIG_FILE constants
```

### Core Classes

- **PDFProcessorApp** (gui/main_window.py): Main GUI application class - handles all GUI layout and user interaction
- **PDFProcessor** (core/pdf_processor.py): PDF file operations and validation
- **FilenameParser** (core/filename_parser.py): Filename parsing and text cleaning
- **ExcelManager** (core/excel_manager.py): Excel file operations and formatting
- **ConfigManager** (core/config.py): Application configuration persistence
- **ToolTip** (gui/utils.py): GUI tooltip utility

## Key Features

1. **PDF Processing**: Extract text from PDF files using PyPDF2
2. **Filename Generation**: Parse PDF content to generate structured filenames
3. **Excel Integration**: Update Excel spreadsheets with extracted information
4. **Configuration Management**: Save/load user preferences and settings
5. **Modern GUI**: Built with ttkbootstrap for modern appearance

## Configuration

The application uses JSON configuration stored in `pdf_processor_config.json` with:
- Excel file path
- Last PDF directory
- Window geometry
- Theme settings
- Locked field configurations

## Refactoring Status

**COMPLETED** - Successfully refactored from single file to modular structure:

### Completed:
- ✅ Created modular folder structure
- ✅ Extracted core classes: ConfigManager, PDFProcessor, FilenameParser, ExcelManager
- ✅ Extracted GUI utilities: ToolTip
- ✅ Created constants file
- ✅ Created gui/main_window.py with PDFProcessorApp class and proper imports
- ✅ Created main app.py entry point
- ✅ Added proper imports to all extracted modules
- ✅ Fixed icon path reference
- ✅ Tested the refactored application - all modules import successfully
- ✅ Set up GitHub repository with proper .gitignore
- ✅ Implemented new versioning system starting with v1.1.0

### Refactoring Results:
- **GUI Layout Preserved**: The PDFProcessorApp class and all GUI components remain exactly as they were in the original file
- **Functionality Preserved**: All methods and features work identically to the original
- **Modular Structure**: Code is now organized into logical modules for better maintainability
- **Original file**: "APP DJs Timeline-verktyg v170 FUNKAR.py" can be kept as reference or backup

### Completed Solutions:
- ✅ **v1.1.1**: Added enhanced bindings for Ctrl+A, Ctrl+V, Delete, BackSpace
- ✅ **v1.1.2**: Implemented custom undo/redo stack for Text widgets
- ✅ **Hybrid system**: Custom stack for problematic operations, tkinter's built-in for normal editing
- ✅ **Preserved functionality**: Entry widgets still work as before
- ✅ **v1.7.4** Excel hybrid method successfully implemented in Excel writing
- ✅ **v1.8.2 - v1.8.8**: Multiple attempts to fix window height for laptop compatibility
- ✅ **v1.9.0**: Added Windows DPI awareness to fix geometry detection issues
- ✅ **v1.9.1**: Fixed laptop status bar visibility by reducing Excel area padding  

## Excel hybrid methods
v1.7.4 contains the COMPLETE WORKING Excel hybrid method. 
These methods solved persistant problems that the app had with writing corrextly formatted text to excel cells. 
The breakthrough hybrid approach consista of:
- openpyxl for reading existing Excel data (preserves formulas)  
- xlsxwriter for writing new data (handles rich text perfectly)
- Method 2 character-by-character algorithm for text extraction
This method might seem complicated but is important to understand that this is the only way we've found to make the app to write perfect Excel rich text formatting with colors, bold, italic, line breaks. 

## Current Issues (v1.9.1)

### Window Height/Layout Problem
**CURRENT STATUS**: Partially solved with significant trade-offs
- ✅ **Laptop screens**: Status bar now visible, app fully functional
- ❌ **External monitors**: Window too short (800px max), buttons cut off, app unusable

**Technical Details:**
- Window height limited to 75% of available height, min 700px, max 800px
- Added Windows DPI awareness: `ctypes.windll.shcore.SetProcessDpiAwareness(2)`
- Reduced padding in Excel integration areas (Group 3/4) from 15px to 8px
- Status bar visibility achieved by reducing vertical spacing throughout Excel sections

**Root Cause Identified**: The excessive padding in Excel integration area was pushing the status bar off-screen on laptop displays. The solution worked for laptops but created new problems for external monitors.

**FUTURE SOLUTION NEEDED**: Dynamic height adjustment based on actual screen size rather than fixed maximum limits.

## Future Refactoring Opportunities

### File Size Issue: main_window.py (2930 lines)
The `gui/main_window.py` file has grown to 2930 lines, making it too large for Claude Code to read efficiently in a single operation. This limits Claude's ability to understand and modify the codebase effectively.

**Recommended Splitting Approach (in order of safety):**

1. **Extract Dialog Classes** (Safest - Recommended First Step)
   - Create `gui/dialogs.py` 
   - Move dialog methods: `show_program_help()`, `show_excel_help()`, `create_excel_template()`
   - Move all paste/truncate dialog methods
   - **Impact**: Remove ~500-800 lines safely without touching core layout

2. **Extract Excel Field Management** (Medium Safe)
   - Create `gui/excel_fields.py`
   - Move `create_excel_fields()`, `setup_excel_field_widget()` and related logic
   - **Impact**: Remove ~300-500 lines

3. **Extract Event Handlers** (Medium Safe)
   - Create `gui/event_handlers.py`
   - Move button click handlers, file selection methods, copy/paste handlers
   - **Impact**: Varies based on scope

4. **Extract GUI Group Creation** (Riskiest but Biggest Impact)
   - Move `create_group1()`, `create_group2()`, etc. to separate files
   - **Risk**: Touches core layout logic, requires careful handling

**Benefits**: Improved maintainability, better Claude Code compatibility, cleaner code organization.

## Important Development Rules
- **Never edit** `APP DJs Timeline-verktyg v170 FUNKAR.py` - this is the old single-file version (kept as backup)
- **Always use** `app.py` as the starting point for the refactored modular version
- **Never** try to change the Excel hybrid methods without asking the user. 
- The GUI layout and functionality must be preserved exactly as designed
- Any changes should be made to the modular files in core/ and gui/ directories
- **Window geometry issues**: Be very careful with height limits - what works for laptops may break external monitors

## Development Notes

- All GUI components are built using ttkbootstrap
- Logging is configured for debugging
- No automated tests are present in the codebase
- No build process required - runs directly with Python interpreter