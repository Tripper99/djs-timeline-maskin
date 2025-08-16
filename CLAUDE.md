# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python desktop application called "DJs Timeline-maskin" (DJs Timeline Machine). It is designed to help investigative journalists and researchers to quickly renaming pdf files and/or create timelines i excel. The first part of the app processes PDF files extracts different parts of the filename. User can then edit these parts and rename the file. It is also possible to copy the old or new file name to the second part of the app: The excel integration. Here the user can add information to a number of fields. By cklicking a button user can then both rename the pdf-file and add a row to a selected excel-document. 
A third way to use the app is by manually add content to excel-fields and create a new excel row without any pdf file selected or renamed. This is practical for researchers whon for example is picking information from books or other sources. 
The application has been refactored from a single large file into a modular structure.

## Current Status (v2.2.13)

**Font Size Field Stability Fix (v2.2.13)**:
- Fixed critical issue where Note1-3 fields were growing when changing font size
- Added grid weight constraints to Note fields matching Händelse field behavior
- Now only text size changes while field dimensions remain stable across all font sizes (9pt, 12pt, 15pt)
- Solution: Added `grid_rowconfigure(row+2, weight=1)` to Note1, Note2, Note3 fields in excel_fields.py

**Space Optimization & Session Persistence Achievement (v2.2.7-v2.2.11)**:
- Successfully optimized GUI for maximum space efficiency on lower resolution screens
- Eliminated unnecessary padding and decorative elements while maintaining functionality
- Implemented inline character counters saving ~4 rows of vertical space
- Added auto-disappearing placeholder text for improved user guidance (YYYY-MM-DD, HH:MM)
- Created clear visual hierarchy with prominent action buttons using color coding
- Fixed session persistence issues: color button states and column width memory

**Major UI/UX Improvements (v2.2.7-v2.2.11)**:
- **Orange copy button**: "↓ Kopiera ned filnamnet till Excelfältet ↓" with arrows and distinctive color for clear workflow indication
- **Enlarged operation buttons**: Save/Reset buttons made 200x40/180x40 pixels for better prominence
- **Reorganized operations area**: Color selection and buttons in separate light grey containers under Händelse field
- **Compact statistics**: Changed from "PDF:er öppnade: X" to "PDF: X" format with smaller font
- **Visual separation**: Different background colors between sections (gray90, gray88, gray86) for better organization
- **Removed obsolete elements**: Theme menu removed (not applicable to CustomTkinter)

**Session Persistence Features (v2.2.11)**:
- **Column width memory**: Excel column sash positions saved to config and restored on startup
- **Color button state consistency**: Visual selection state properly resets after save operations
- **Proportional scaling**: Saved column positions adapt to different screen sizes automatically
- **Smart fallbacks**: New users get sensible 40/30/30 defaults, existing users keep preferences

**Comprehensive Testing Implementation (v2.2.3)**:
- Successfully implemented complete test suite with 120 tests total
- Phase 1: 115 autonomous unit tests covering core business logic (filename_parser, pdf_processor, excel_manager, config)
- Phase 2: 5 semi-autonomous integration tests covering complete user workflows
- Tests achieve 96% autonomous coverage with 4% requiring user verification
- Created TESTING_GUIDE.md with comprehensive documentation for future development workflow
- All tests pass and provide robust foundation for safe refactoring and feature development

**Major Architectural Achievement (v2.2.2)**:
- Successfully modularized main_window.py from 35,000+ tokens into 7 specialized mixin modules
- Achieved exceptional code organization with clean separation of concerns
- Created PDFOperationsMixin, ExcelOperationsMixin, LayoutManagerMixin, EventHandlersMixin, UndoManagerMixin, FormattingManagerMixin, and StatsManagerMixin
- Main window reduced from ~3000 lines to 384 lines with identical functionality
- Excel hybrid operations preserved exactly without any modifications
- All functionality tested and verified working perfectly

**Key Technical Solutions**:
- **Space optimization**: Inline counters, reduced padding, compact labels
- **Placeholder text**: Manual Entry-StringVar binding to preserve CustomTkinter placeholder functionality
- **Session persistence**: Config-based saving/restoration of UI state (sash positions, color states)
- **Visual hierarchy**: Color-coded buttons (orange=transfer, green=save, blue=reset) for clear workflow
- **Modular architecture**: Clean mixin inheritance with no circular dependencies

**Testing Notes**:
- Comprehensive test suite available: `python -m pytest tests/ -v`
- Always run Ruff syntax check before committing: `ruff check . --fix`
- Run integration tests before releases: `python -m pytest tests/test_integration_workflows.py -v -s`
- See TESTING_GUIDE.md for complete testing workflow procedures
- Test application startup after layout changes
- Critical: Always test placeholder text visibility and session persistence features

## Additional guideline on github commit
**Never* mention yourself (Claude) in comment when doing commit. *Never* write stuff like "🤖 Generated with [Claude Code](https://claude.ai/code) Co-Authored-By: Claude <noreply@anthropic.com>". 

## Working Principles

- **Honest Collaboration Guideline**: 
  * Prioritize technical accuracy. Point out bugs, inefficiencies, and better approaches immediately. 
  * Confirm understanding with minimal acknowledgment. Focus on code quality, performance, and maintainability. 
  * Challenge bad ideas with specific alternatives.
  
  [... rest of the existing content remains unchanged ...]