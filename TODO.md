# TODO List - DJs Timeline-maskin

## High Priority - Code Quality

### 1. Split main_window.py into smaller, focused modules ✅
- [x] Current file is 35,000+ tokens - needs modularization
- [x] Suggested split:
  - [x] PDF operations module (gui/pdf_operations.py)
  - [x] Excel operations module (gui/excel_operations.py)
  - [x] Layout management module (gui/layout_manager.py)
  - [x] Event handlers module (gui/event_handlers.py)
  - [x] Statistics and state management module (gui/stats_manager.py)
  - [x] Undo/redo functionality module (gui/undo_manager.py)
  - [x] Text formatting module (gui/formatting_manager.py)

### 2. Update requirements.txt to include all dependencies ✅
- [x] Add xlsxwriter (now included)
- [x] Add customtkinter (now included)
- [x] Verify all other dependencies are listed with correct versions

## Medium Priority - Testing & Documentation

### 3. Expand testing beyond layout tests
**Implementation Strategy:**

#### Phase 1: Autonomous Tests (80-90% automation, zero user involvement) ✅ **COMPLETED**
- [x] **Core Business Logic Tests** (Fully Autonomous):
  - [x] Test filename_parser.py - parsing logic, filename construction, text cleaning (33 tests)
  - [x] Test pdf_processor.py - validation, page counting, file operations (30 tests)
  - [x] Test excel_manager.py - Excel operations, column mapping, data writing (31 safe tests)
  - [x] Test config.py - JSON loading/saving, configuration management (21 tests)
- [ ] **Unit Tests for Individual Mixins** (Mostly Autonomous):
  - [ ] Test PDF Operations Mixin - file selection logic, validation, renaming
  - [ ] Test Excel Operations Mixin - row creation, column mapping
  - [ ] Test Event Handlers - event processing logic (mocked GUI interactions)
  - [ ] Test Undo/Redo - command pattern implementation

**Phase 1 Results**: 115 tests created, all passing autonomously with zero user involvement

#### Phase 2: Semi-Autonomous Tests (User review needed, ~15-30 min per run) ✅ **COMPLETED**
- [x] **Integration Testing**:
  - [x] Complete PDF-to-Excel workflow (auto-test + user verification)
  - [x] Manual Excel entry workflow
  - [x] File renaming with real PDFs
  - [x] Configuration persistence across app restarts
- [x] **Real-World Data Testing**:
  - [x] Test with user-provided sample PDF files
  - [x] Test with typical Excel templates
  - [x] Test with various configuration scenarios

**Phase 2 Results**: 5 integration tests created, covering complete workflows with detailed output for user verification

#### Phase 3: Manual Verification Tests (User active participation)
- [ ] **Visual/Layout Testing**:
  - [ ] Column resizing functionality
  - [ ] Field focus behaviors and highlighting
  - [ ] Dialog positioning and appearance
  - [ ] Theme and styling verification
- [ ] **Error Scenario Testing**:
  - [ ] Corrupted PDF handling
  - [ ] Locked Excel file scenarios
  - [ ] Invalid configuration recovery

## Current Bugs to Fix

### 1. Custom Field Names Not Displaying in UI (v2.3.0) ✅ **FIXED in v2.3.3**
**Problem**: Custom field names are saved correctly but not displayed in the UI after applying changes.

**Root Cause Identified**: `_on_field_config_applied()` method called `clear_config()` which deleted the entire config file immediately after custom names were saved to it.

**Solution Implemented (v2.3.3)**:
- Removed `self.config_manager.clear_config()` from `_on_field_config_applied()` method
- Changed from complete config deletion to selective user data clearing only
- Preserved config file containing custom field names during field configuration reset
- Added comprehensive debug logging throughout custom field name data flow

**Result**: Custom field names now persist correctly and display immediately in main UI after Apply.

### 2. Font Size Bug - Händelse Only (v2.3.3)
**Problem**: All font size change buttons only affect Händelse field, not Note1-3 fields.
**Expected**: Font size buttons should change text size in all text fields (Händelse, Note1, Note2, Note3).
**Impact**: Users cannot adjust font size for note fields, reducing usability for longer text entry.

## Future Improvements

### 4. Consider async operations for file processing
- [ ] Evaluate if PDF processing could benefit from async operations
- [ ] Consider background processing for large Excel files
- [ ] Implement progress indicators for long operations

### 5. Field Configuration Dialog Enhancements
**Field Name Templates System**:
- [ ] Add "Återställ till standard" (Restore to default names) button - clears all custom name fields
- [ ] Add "Spara namnmall" (Save name template) button - saves current field configuration as template
- [ ] Add "Ladda namnmall" (Load name template) button - loads previously saved template
- [ ] Add "Spara namnmall som..." (Save name template as...) button - save with custom template name
- [ ] Display current template name (if template has been saved/loaded)
- [ ] Enable "Spara namnmall" only when at least one field has been changed from current state
- [ ] Create template storage system (JSON files or config section)

**Dialog Visual Improvements**:
- [ ] Fix the overall look and feel of the field name config window
- [ ] Improve button layout and spacing
- [ ] Enhance visual feedback for template operations
- [ ] Add template management section to dialog

### 6. Add type hints throughout the codebase
- [ ] Add type hints to all function signatures
- [ ] Add type hints for class attributes
- [ ] Use typing module for complex types
- [ ] Consider using mypy for type checking

## Completed Tasks ✅
- [x] Implement resizable columns (v2.2.0)
- [x] Fix persistent gap above Händelse field (v2.1.9)
- [x] Achieve proper 40/30/30 column distribution (v2.1.8)
- [x] Make UI more compact with reduced padding
- [x] Move date/time fields to top of left column
- [x] Update requirements.txt to include all dependencies (xlsxwriter, customtkinter)
- [x] Create comprehensive test suite (120 tests total):
  - [x] Phase 1: 115 autonomous unit tests for core modules
  - [x] Phase 2: 5 semi-autonomous integration tests for complete workflows
- [x] Create TESTING_GUIDE.md documentation for future test usage
- [x] **UI Optimization for Lower Resolution Screens (v2.2.7-v2.2.11)**:
  - [x] Change button texts for clearer workflow indication
  - [x] Add direct Excel creation button
  - [x] Remove obsolete theme menu
  - [x] Implement space-saving inline character counters (~4 rows saved)
  - [x] Add color-coded button system (orange=transfer, green=save, blue=reset)
  - [x] Enlarge action buttons for better accessibility
  - [x] Add placeholder text for date/time fields
  - [x] Implement session persistence for column widths and color button states
  - [x] Fix critical startup bug (checp_dependencies → check_dependencies)
  - [x] Enhance user guidance with comprehensive tooltips
- [x] **Font Size Field Stability Fix (v2.2.13)**:
  - [x] Fixed Note1-3 fields growing when changing font size
  - [x] Added grid weight constraints to maintain stable field dimensions
  - [x] Ensured only text size changes, not field physical size
- [x] **Time Field Validation UX Fix (v2.2.15)**:
  - [x] Fixed time fields trapping users with validation errors on focus loss
  - [x] Made time field behavior consistent with date fields
  - [x] Removed aggressive FocusOut validation binding from time fields
  - [x] Maintained data validation integrity during save operations
  - [x] Used bug-finder-debugger agent for systematic root cause analysis
- [x] **Custom Field Names Display Bug Fix (v2.3.3)**:
  - [x] Fixed critical bug where custom field names were saved but not displayed in UI
  - [x] Identified root cause: config file deletion immediately after saving custom names
  - [x] Removed config deletion from field configuration apply process
  - [x] Added comprehensive debug logging for custom field name data flow
  - [x] Verified fix works for both first-time and existing users