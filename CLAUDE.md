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

## Modular Refactoring Progress

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
- All functionality preserved, GUI layout unchanged
- **Result**: v1.9.3 tested and confirmed working perfectly

### Phase 2: Excel Field Management (v1.9.4) - ❌ LAYOUT BROKEN
**Goal**: Extract Excel field creation and management from main_window.py
**Status**: Code extraction completed but GUI layout severely broken

**Implementation Details:**
- Created `gui/excel_fields.py` with `ExcelFieldManager` class  
- Extracted 6 Excel field methods (~400-500 lines from main_window.py):
  - `collect_locked_field_data()` - Collects locked field states and contents
  - `restore_locked_fields()` - Restores saved locked field data
  - `save_locked_fields_on_exit()` - Saves locked fields before exit
  - `clear_excel_fields()` - Clears non-locked Excel fields
  - `create_excel_fields()` - Creates dynamic Excel fields layout
  - `create_field_in_frame()` - Creates individual field widgets
- Updated main_window.py to use `self.excel_field_manager.method()` pattern

**Critical Problem Discovered:**
The Excel fields section GUI is severely broken after Phase 2 implementation:
- **Vertical compression**: Excel fields area much too short, most fields not visible
- **Horizontal compression**: Three-column layout (Grundinformation, Huvudinnehåll, Anteckningar) squished together
- **Layout system changed**: Working v1.9.3 grid-based layout was replaced with canvas-based scrollable layout
- **Application unusable**: Cannot access most Excel fields

**Root Cause Analysis:**
Code comparison between working v1.9.3 and broken v1.9.4 revealed fundamental layout system changes:

| Aspect | v1.9.3 (Working) | v1.9.4 (Broken) |
|--------|------------------|------------------|
| Layout System | `grid()` with equal columns | `pack()` with canvas |
| Container | `tb.Frame` with grid | Canvas + scrollable frame |
| Column Distribution | `uniform="col"` for exact 1/3 width | `side="left"` packing |
| Field Creation | `(parent, col_name, row, column_type)` | `(parent, col_name, field_type)` |

**Solution Plan:**
Instead of debugging the broken new layout system, restore the proven working layout code from v1.9.3:
1. Replace `create_excel_fields()` method in `ExcelFieldManager` with exact v1.9.3 working version
2. Replace `create_field_in_frame()` method with working grid-based version
3. Maintain the manager pattern but use proven working layout logic
4. Test immediately to confirm layout restoration

**Detailed Technical Changes Required in gui/excel_fields.py:**

**1. Replace create_excel_fields() method completely:**
- Remove canvas-based scrollable layout (lines 142-202)
- Replace with v1.9.3 grid-based layout using `fields_container = tb.Frame(self.parent.excel_fields_frame)`
- Use `fields_container.grid_columnconfigure(0/1/2, weight=1, uniform="col")` for equal 1/3 width columns
- Create three LabelFrames using `grid()` instead of `pack()` with `side="left"`
- Use column groupings from v1.9.3:
  - column1_fields: ['OBS', 'Inlagd datum', 'Kategori', 'Underkategori', 'Person/sak', 'Egen grupp', 'Dag', 'Tid start', 'Tid slut', 'Källa1', 'Källa2', 'Källa3', 'Övrigt']
  - column2_fields: ['Händelse'] 
  - column3_fields: ['Note1', 'Note2', 'Note3']
- Call `create_field_in_frame(frame, col_name, row, column_type)` with row counter and column_type parameter

**2. Replace create_field_in_frame() method completely:**
- Change method signature from `(parent_frame, col_name, field_type)` to `(parent_frame, col_name, row, column_type="column1")`
- Remove pack-based layout, use grid-based layout with row positioning
- Handle different column types:
  - column1: horizontal layout `grid(row=row, column=0/1/2)` for label/entry/lock
  - column2&3: vertical layout with header_frame for label+lock
- Use Text widgets for text fields (Note1-3, Händelse), StringVar for others
- Implement proper grid row configuration with `parent_frame.grid_rowconfigure(row+X, weight=1)` for expandable fields
- Return number of rows used (1 for entries, 4 for text fields)
- Restore formatting toolbar creation and character counter positioning
- Use proper event bindings and undo handling from v1.9.3

**3. Excel variables handling:**
- In create_excel_fields(), clear and recreate `self.parent.excel_vars` 
- Use StringVar for most fields, Text widgets stored directly for text fields
- Auto-fill today's date in "Inlagd datum" field

**4. Import and method dependencies:**
- Ensure all required imports are present (datetime, tk.Text handling)
- Verify that parent app methods are accessible (enable_undo_for_widget, setup_text_formatting_tags, create_formatting_toolbar, etc.)

**5. Testing checklist after changes:**
- Three columns display with equal 1/3 width distribution
- All Excel fields visible and properly sized
- Text fields (Händelse, Note1-3) have proper height and character counters
- Lock switches work correctly
- Field creation follows v1.9.3 column groupings
- Responsive layout works on different screen sizes

### Future Phases (Planned)
3. **Extract Event Handlers** (Medium Safe)
4. **Extract GUI Group Creation** (Riskiest but Biggest Impact)

**Current Priority**: Fix Phase 2 layout issues before proceeding with additional phases.

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