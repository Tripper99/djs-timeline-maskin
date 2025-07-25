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

## Rich Text Format Preservation (v1.14.0)
**NEW SYSTEM**: Complete format preservation for locked text fields across app sessions

### Text Fields with Format Preservation
The following 4 text fields support rich text formatting and preservation:
- **Note1** - Research notes with formatting
- **Note2** - Additional notes with formatting  
- **Note3** - Supplementary notes with formatting
- **Händelse** - Event description with formatting

### Supported Formatting
- **Bold** - Applied via toolbar "B" button
- **Italic** - Applied via toolbar "I" button
- **Colors** - Applied via toolbar color buttons:
  - **Red** (R button)
  - **Blue** (B button) 
  - **Green** (G button)
  - **Black** (K button)

### Format Storage System
Rich text formatting is stored as JSON-compatible tag ranges in the configuration file:
```json
"locked_field_formats": {
  "Note1": [
    {
      "tag": "bold",
      "start": "1.0",
      "end": "1.25"
    },
    {
      "tag": "red", 
      "start": "2.0",
      "end": "2.50"
    }
  ]
}
```

### Technical Implementation
- **Tag Serialization**: `serialize_text_widget_formatting()` scans tkinter Text widgets for formatting tags
- **Position Storage**: Tag ranges stored as tkinter index positions (line.character format)
- **Format Restoration**: `restore_text_widget_formatting()` reapplies tags on app startup
- **Selective Processing**: Only locked fields with formatting are serialized
- **Error Handling**: Invalid tag positions are safely ignored during restoration

### Usage Workflow
1. Apply formatting to text using toolbar buttons
2. Lock the field using the lock switch
3. Close the app (formatting automatically saved)
4. Restart the app (formatting automatically restored)

## Current Status (v1.15.3)

**NEW MASTER VERSION**: Refined date/time field layout with proper alignment and positioning
- ✅ **Date/Time Field Layout**: Polished two-column subgroup above Händelse with perfect alignment
- ✅ **Field Alignment**: Grid-based layout ensures consistent positioning of labels, entries, and lock switches
- ✅ **Header Positioning**: Händelse header properly positioned directly above formatting toolbar
- ✅ **Rich Text Persistence**: Bold, italic, and color formatting preserved across app sessions
- ✅ **Locked Field Formatting**: Text formatting in Note1, Note2, Note3, Händelse saved/restored
- ✅ **Time Fields**: Starttid and Sluttid with HH:MM validation and auto-formatting (HHMM→HH:MM)
- ✅ **19 Excel Columns**: All original fields plus new time fields (was 17, now 19)
- ✅ **Core Functionality**: PDF processing, Excel integration, locked fields all working
- ✅ **Layout**: Three-column Excel fields display correctly with time fields in column 2
- ✅ **Mixed Rich Text**: Format changes within text work correctly in Excel
- ⚠️ **Uniform Rich Text Bug**: Single format text disappears in Excel output (see Known Issues below)

## Known Issues

### Rich Text Uniform Formatting Bug (Excel Export Only)
**STATUS**: Partial functionality in Excel export - mixed formats work, uniform formats fail
**NOTE**: This bug only affects Excel output. GUI formatting and persistence work perfectly.

**What Works**:
- ✅ Mixed formatting displays correctly (e.g., plain text followed by red text)
- ✅ Format changes within text preserve all formatting correctly
- ✅ All text content is preserved and visible in Excel cells
- ✅ Complex combinations work (e.g., plain + red + blue text)

**What Doesn't Work**:
- ❌ Single uniform formatting disappears (e.g., text that is only red)
- ❌ Combined uniform formatting disappears (e.g., text that is only bold + red)
- **Pattern**: Text disappears if there's only one format applied to entire cell content

**Technical Note**: The issue is in the xlsxwriter rich text API handling of uniform formatting in `core/excel_manager.py`. There needs to be a change of format within the text for it to be preserved.

### Window Height on External Monitors
**STATUS**: Functional workaround in place
- ✅ **Laptop screens**: Full functionality, all elements visible
- ⚠️ **External monitors**: Slightly shortened window (800px max) but fully functional
- **Impact**: Minimal - all features accessible, status bar visible
- **Future improvement**: Dynamic height adjustment based on screen size

## Things That Remain To Do

### High Priority Issues
1. **Rich Text Uniform Formatting Bug** (Excel Export)
   - **Status**: Affects Excel output only, GUI works perfectly
   - **Issue**: Text with uniform formatting (all red, all bold) disappears in Excel
   - **Location**: `core/excel_manager.py` xlsxwriter rich text API handling
   - **Workaround**: Use mixed formatting within text

2. **Code Quality Improvements**
   - **Ruff Warnings**: 96 style/import warnings to clean up
   - **Location**: Multiple files, mostly whitespace and import organization
   - **Impact**: No functional issues, but affects code maintainability

### Medium Priority Enhancements
3. **Window Height Optimization**
   - **Goal**: Dynamic height adjustment based on screen size
   - **Current**: Fixed 800px max height workaround
   - **Impact**: Slightly shortened window on large external monitors

4. **Performance Optimizations**
   - **GUI Responsiveness**: Consider lazy loading for large Excel files
   - **Memory Usage**: Review memory footprint for long sessions

### Low Priority Future Features
5. **Excel Macro Support** (.xlsm files)
   - **Status**: Previously attempted but reverted due to hybrid method conflicts
   - **Challenge**: Cannot compromise critical hybrid Excel writing approach
   - **Alternative**: Consider separate handling for .xlsm vs .xlsx files

6. **Enhanced Rich Text Features**
   - **Underline Support**: Add underline formatting option
   - **Font Size Control**: Variable font sizes within text fields
   - **Additional Colors**: Expand color palette beyond current 4 colors

7. **User Experience Improvements**
   - **Keyboard Shortcuts**: More comprehensive shortcut support
   - **Drag & Drop**: PDF file drag and drop functionality
   - **Undo/Redo**: Enhanced undo system across all components

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
- **Current version**: v1.15.3 (stable master with refined date/time field layout and perfect positioning)
- **Last tested**: 2025-07-25 - Refined date/time field layout working perfectly, all functionality stable

## Recent Development History

### v1.15.3 Success (2025-07-25) - Final Header Positioning Fix
**Achievement**: Perfect positioning of Händelse header directly above toolbar

**Layout Fix**:
- ✅ **Header Positioning**: Changed sticky parameter to "sew" (south-east-west)
- ✅ **Visual Flow**: Header now sits directly above formatting toolbar as intended
- ✅ **Professional Appearance**: Clean transition from date/time fields to Händelse section

**Technical Implementation**:
- Modified header_frame sticky parameter from "new" to "sew"
- Header anchors to bottom of expandable row, placing it above toolbar
- Maintains proper spacing and visual hierarchy

### v1.15.2 (2025-07-25) - Header Positioning Attempt
**Goal**: Fix Händelse header vertical centering issue
**Result**: Header stuck at very top (overcorrection)
**Lesson**: Need bottom alignment, not top alignment

### v1.15.1 Success (2025-07-25) - Date/Time Field Alignment Refinement
**Achievement**: Perfected symmetrical alignment of date/time fields

**Alignment Improvements**:
- ✅ **Grid-Based Layout**: Replaced pack with grid for precise positioning
- ✅ **Fixed Label Width**: Set minsize=85px for consistent label alignment
- ✅ **Column Structure**: Organized as Label | Entry | Lock Switch
- ✅ **Visual Symmetry**: Perfect alignment between left/right columns

**Technical Implementation**:
- Implemented grid layout with fixed column widths
- Left column: Startdatum + Starttid with consistent spacing
- Right column: Slutdatum + Sluttid with matching alignment
- Increased inter-column spacing (10px) for better visual separation

### v1.15.0 Success (2025-07-25) - Initial Date/Time Field Layout
**Achievement**: Successfully implemented two-column subgroup for date/time fields

**New Features Added**:
- ✅ **Two-Column Subgroup**: Date/time fields organized in a compact 2x2 grid above Händelse
- ✅ **Space Optimization**: Date/time fields only use minimal required space
- ✅ **Better Visual Grouping**: Related fields (start date/time, end date/time) side by side
- ✅ **Händelse Expansion**: Händelse field now gets all remaining vertical space

**Technical Implementation**:
- Created `_create_datetime_fields_in_subframe()` method for specialized layout
- Modified column 2 structure with fixed-height date/time row (weight=0)
- Händelse placed in expandable row (weight=1) to fill available space
- Left column: Startdatum + Starttid with lock switches
- Right column: Slutdatum + Sluttid with lock switches

**Layout Benefits**:
- More efficient use of vertical space in middle column
- Logical grouping of related date/time fields
- Maximum space for Händelse text entry
- All functionality preserved (validation, lock switches, etc.)

### v1.14.0 Success (2025-07-25) - Rich Text Format Preservation
**Achievement**: Successfully implemented rich text format preservation for locked fields

**New Features Added**:
- ✅ **Rich Text Persistence**: Bold, italic, and color formatting preserved across app sessions
- ✅ **Format Serialization**: Tkinter text tags converted to JSON-compatible format
- ✅ **Locked Field Enhancement**: Note1, Note2, Note3, Händelse fields preserve formatting when locked
- ✅ **Configuration Integration**: Format data stored in new "locked_field_formats" config section
- ✅ **Backward Compatibility**: Works seamlessly with existing configuration files

**Technical Implementation**:
- `serialize_text_widget_formatting()`: Converts tkinter tags to JSON format
- `restore_text_widget_formatting()`: Restores tags from JSON data
- Updated `collect_locked_field_data()` to include formatting data
- Updated `restore_locked_fields()` to apply saved formatting
- Support for tags: bold, italic, red, blue, green, black

**Testing Results**:
- ✅ **Perfect Format Preservation**: All tested formatting combinations work correctly
- ✅ **Mixed Formatting**: Complex combinations within single field preserved
- ✅ **Session Persistence**: Formatting survives app close/restart cycles
- ✅ **Error Handling**: Safe recovery from invalid tag positions
- ✅ **Performance**: Minimal overhead, only processes locked fields with formatting

### v1.13.0 Success (2025-07-25) - Time Fields Implementation
**Achievement**: Successfully implemented time fields with validation while preserving Excel hybrid method

**New Features Added**:
- ✅ **Starttid and Sluttid fields**: HH:MM format with auto-formatting and validation
- ✅ **Time validation**: 24-hour format (00:00-23:59) with HHMM→HH:MM conversion
- ✅ **19 Excel columns**: Expanded from 17 to include new time fields
- ✅ **Column 2 layout**: Time fields positioned above Händelse field
- ✅ **Lock switches**: Added for new time fields (17 total lock states)

**Preserved Functionality**:
- ✅ **Excel hybrid method**: Sacred v1.7.4 approach maintained
- ✅ **GUI layout**: Three-column structure with proper field distribution
- ✅ **Mixed rich text**: Format changes within text work correctly

### Critical Reversion History (2025-07-24)
**Background**: Previous attempt (v1.9.12) broke Excel hybrid method with automatic header migration and direct openpyxl saving calls. Complete reversion to v1.9.8 was required to restore working baseline.

**Key Lesson**: Excel hybrid method changes require explicit user permission and thorough testing.