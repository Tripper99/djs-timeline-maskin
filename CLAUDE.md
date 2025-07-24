# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python desktop application called "DJs Timeline-maskin" (DJs Timeline Machine). It is designed to help investigative journalists and researchers to quickly renaming pdf files and/or create timelines i excel. The first part of the app processes PDF files extracts different parts of the filename. User can then edit these parts and rename the file. It is also possible to copy the old or new file name to the second part of the app: The excel integration. Here the user can add information to a number of fields. By cklicking a button user can then both rename the pdf-file and add a row to a selected excel-document. 
A third way to use the app is by manually add content to excel-fields and create a new excel row without any pdf file selected or renamed. This is practical for researchers whon for example is picking information from books or other sources. 
The application has been refactored from a single large file into a modular structure.

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
- ✅ **v1.9.3**: Completed Phase 1 refactoring - extracted DialogManager successfully
- ✅ **v1.9.5**: Completed Phase 2 refactoring - extracted ExcelFieldManager with layout fix

## Excel hybrid methods
v1.7.4 contains the COMPLETE WORKING Excel hybrid method. 
These methods solved persistant problems that the app had with writing corrextly formatted text to excel cells. 
The breakthrough hybrid approach consista of:
- openpyxl for reading existing Excel data (preserves formulas)  
- xlsxwriter for writing new data (handles rich text perfectly)
- Method 2 character-by-character algorithm for text extraction
This method might seem complicated but is important to understand that this is the only way we've found to make the app to write perfect Excel rich text formatting with colors, bold, italic, line breaks. 

## Current Status (v1.9.5)

**STABLE VERSION**: All major refactoring phases completed successfully
- ✅ **Phase 1**: Dialog extraction (v1.9.3) - Working perfectly
- ✅ **Phase 2**: Excel field extraction (v1.9.5) - Layout fixed and tested
- ✅ **Layout**: Three-column Excel fields display correctly with equal 1/3 width distribution
- ✅ **Functionality**: All features working - PDF processing, Excel integration, locked fields
- ✅ **DPI Awareness**: Windows scaling issues resolved

### Known Minor Issue: Window Height on External Monitors
**STATUS**: Functional workaround in place
- ✅ **Laptop screens**: Full functionality, all elements visible
- ⚠️ **External monitors**: Slightly shortened window (800px max) but fully functional
- **Impact**: Minimal - all features accessible, status bar visible
- **Future improvement**: Dynamic height adjustment based on screen size

## Modular Refactoring Progress - COMPLETED ✅

### Phase 1: Dialog Extraction (v1.9.3) - ✅ COMPLETED SUCCESSFULLY
**Goal**: Extract dialog management from main_window.py to improve code organization
**Status**: Successfully completed and tested - application works perfectly

**Implementation Details:**
- Created `gui/dialogs.py` with `DialogManager` class
- Extracted 4 dialog methods (~540 lines removed from main_window.py):
  - `show_excel_help()` - Excel file requirements dialog
  - `create_excel_template()` - Creates new Excel template files
  - `handle_paste_event()` - Smart paste handling with length checking
  - `handle_text_splitting()` - Splits long text across multiple fields
- Updated main_window.py to use `self.dialog_manager.method()` pattern
- **Result**: v1.9.3 tested and confirmed working perfectly

### Phase 2: Excel Field Management (v1.9.5) - ✅ COMPLETED SUCCESSFULLY
**Goal**: Extract Excel field creation and management from main_window.py
**Status**: Successfully completed after layout fix - application fully functional

**Implementation Details:**
- Created `gui/excel_fields.py` with `ExcelFieldManager` class  
- Extracted 6 Excel field methods (~400-500 lines from main_window.py):
  - `collect_locked_field_data()` - Collects locked field states and contents
  - `restore_locked_fields()` - Restores saved locked field data
  - `save_locked_fields_on_exit()` - Saves locked fields before exit
  - `clear_excel_fields()` - Clears non-locked Excel fields
  - `create_excel_fields()` - Creates dynamic Excel fields layout
  - `create_field_in_frame()` - Creates individual field widgets
- **Critical Learning**: Initial v1.9.4 broke layout by changing grid-based system
- **Solution**: Restored exact v1.9.3 layout code while maintaining manager pattern
- **Result**: v1.9.5 tested and confirmed - perfect 3-column layout with all functionality

### Future Phases (Optional Improvements)
**Status**: Core refactoring complete, application fully stable

3. **Extract Event Handlers** (Medium complexity)
4. **Extract GUI Group Creation** (High complexity)

**Current Priority**: Application is fully functional and well-organized. Future phases are optional optimizations.

## Important Development Rules
- **Never edit** `APP DJs Timeline-verktyg v170 FUNKAR.py` - this is the old single-file version (kept as backup)
- **Always use** `app.py` as the starting point for the refactored modular version
- **Never** try to change the Excel hybrid methods without asking the user - v1.7.4 contains the only working solution
- **Preserve working code**: When refactoring, extract code exactly as-is, don't "improve" during extraction
- **Test immediately**: After any structural changes, test the application thoroughly
- **Grid layout is sacred**: The three-column Excel fields layout uses grid with `uniform="col"` - never change this
- Any changes should be made to the modular files in core/ and gui/ directories

## Refactoring Lessons Learned
- **Working code is sacred**: During refactoring, preserve exact functionality and layout
- **Extract, don't improve**: Make structural changes separate from functional improvements
- **Test after each step**: Verify functionality before making additional changes
- **Layout systems matter**: Grid-based layouts with `uniform` distribution are critical for UI consistency

## Development Notes

- All GUI components are built using ttkbootstrap
- Logging is configured for debugging
- No automated tests are present in the codebase
- No build process required - runs directly with Python interpreter
- **Current version**: v1.9.5 (stable, fully functional)
- **Last tested**: 2025-07-24 - All features working correctly