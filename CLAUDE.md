# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python desktop application called "DJs Timeline-maskin" (DJs Timeline Machine) that processes PDF files and updates Excel spreadsheets. The application has been refactored from a single large file into a modular structure.

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
pip install ttkbootstrap PyPDF2 openpyxl
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

## Current Work: Text Formatting Issues

**STATUS: PROBLEMS IDENTIFIED** - Text formatting function has critical issues

### Problems Identified:

#### 1. **Disabled Rich Text Feature**
- `gui/main_window.py:2704-2710`: Text formatting is disabled with "TEMPORARY FIX"
- Function `get_formatted_text_for_excel()` only returns plain text instead of formatted RichText objects
- This disables the entire rich text formatting feature added in v1.2.0

#### 2. **Class Name Mismatch**
- Code checks for `'CellRichText'` class name in multiple places:
  - `gui/main_window.py:1524`: Checks for `'CellRichText'`
  - `core/excel_manager.py:75`: Also checks for `'CellRichText'`
- But the actual openpyxl class is `RichText`, not `CellRichText`

#### 3. **Import Issues**
- The RichText import happens inside the function, causing reference issues
- `core/excel_manager.py` references `CellRichText` but doesn't import it properly

#### 4. **Inconsistent Implementation**
- Original git commit `ba727fe` shows proper RichText implementation
- Current code has reverted to plain text due to "Excel corruption" concerns

### Solutions Required:

1. **Fix Class Name References**:
   - Change `'CellRichText'` to `'RichText'` in both files
   - Update `gui/main_window.py:1524` and `core/excel_manager.py:75`

2. **Restore Rich Text Implementation**:
   - Remove the "TEMPORARY FIX" and restore the original rich text extraction code
   - Ensure proper error handling to prevent Excel corruption

3. **Fix Import Structure**:
   - Ensure consistent imports of `RichText` from `openpyxl.cell.text`
   - Add proper error handling for import failures

### Current Version: v1.2.8

### Key Files Affected:
- `gui/main_window.py`: Rich text extraction disabled
- `core/excel_manager.py`: Incorrect class name references
- `utils/constants.py`: Version tracking

### Technical Details:
- Formatting toolbar is functional (Bold, Italic, Colors with keyboard shortcuts)
- Text widget formatting tags work correctly in GUI
- Problem is specifically in converting tkinter tags to Excel RichText objects
- Need to fix the conversion process without breaking Excel file integrity

## Previous Work: Undo/Redo Enhancement

**STATUS: COMPLETED** - Undo/redo functionality fixed in Text widgets

### Completed Solutions:
- ✅ **v1.1.1**: Added enhanced bindings for Ctrl+A, Ctrl+V, Delete, BackSpace
- ✅ **v1.1.2**: Implemented custom undo/redo stack for Text widgets
- ✅ **Hybrid system**: Custom stack for problematic operations, tkinter's built-in for normal editing
- ✅ **Preserved functionality**: Entry widgets still work as before

## Important Development Rules

- **Never edit** `APP DJs Timeline-verktyg v170 FUNKAR.py` - this is the old single-file version (kept as backup)
- **Always use** `app.py` as the starting point for the refactored modular version
- The GUI layout and functionality must be preserved exactly as designed
- Any changes should be made to the modular files in core/ and gui/ directories

## Development Notes

- The application is version v170 (defined in utils/constants.py)
- All GUI components are built using ttkbootstrap
- Logging is configured for debugging
- No automated tests are present in the codebase
- No build process required - runs directly with Python interpreter