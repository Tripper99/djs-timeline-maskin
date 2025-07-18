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

## Current Work: Undo/Redo Enhancement

**STATUS: IN PROGRESS** - Fixing undo/redo functionality in Text widgets

### Problem Identified:
- Text widgets (Händelse, Note1, Note2, Note3) have poor undo/redo for certain operations
- **Ctrl+A + Del + Ctrl+Z**: Text disappears instead of being restored
- **Ctrl+A + Ctrl+V + Ctrl+Z**: Text disappears instead of being restored
- Entry widgets work fine, only Text widgets affected

### Solutions Implemented:
- ✅ **v1.1.1**: Added enhanced bindings for Ctrl+A, Ctrl+V, Delete, BackSpace
- ✅ **v1.1.2**: Implemented custom undo/redo stack for Text widgets
- ✅ **Hybrid system**: Custom stack for problematic operations, tkinter's built-in for normal editing
- ✅ **Preserved functionality**: Entry widgets still work as before

### Current Version: v1.1.2

### Next Steps for Testing:
1. Test Ctrl+A + Del + Ctrl+Z in Text widgets (should restore original text)
2. Test Ctrl+A + Ctrl+V + Ctrl+Z in Text widgets (should restore original text)
3. Verify normal typing + Ctrl+Z still works in Text widgets
4. Verify Entry widgets still work normally
5. If tests pass, mark as completed and update to v1.1.3

### Key Files Modified:
- `gui/main_window.py`: Enhanced undo/redo implementation
- `utils/constants.py`: Version updates
- All changes committed to GitHub repository

### Technical Details:
- Custom undo/redo stacks: `self.text_undo_stacks` and `self.text_redo_stacks`
- Enhanced event handlers: `handle_select_all_undo()`, `handle_paste_undo()`, `handle_delete_with_undo()`
- Fallback system: Custom stack first, then tkinter's built-in system

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