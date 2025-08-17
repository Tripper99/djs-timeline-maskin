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

### 1. Custom Field Names Not Displaying in UI (v2.3.0)
**Problem**: Custom field names are saved correctly but not displayed in the UI after applying changes.

**Root Cause**: `gui/excel_fields.py` (lines 339-343) uses hardcoded field names instead of getting them from field_manager.

**Fix Plan**:
1. Replace hardcoded field name arrays with internal field ID arrays:
   ```python
   # Instead of: column1_fields = ['Startdatum', 'Starttid', ...]  # HARDCODED!
   # Use: column1_field_ids = ['startdatum', 'starttid', ...]  # Internal IDs
   ```

2. Convert IDs to current display names dynamically:
   ```python
   column1_fields = [field_manager.get_display_name(fid) for fid in column1_field_ids]
   column3_fields = [field_manager.get_display_name(fid) for fid in column3_field_ids]
   ```

3. Test that custom names appear correctly in:
   - Column 1 fields (dates, times, categories, etc.)
   - Column 2 field (Händelse - though protected)
   - Column 3 fields (Note1-3)

**Files to modify**: `gui/excel_fields.py` (lines 339-356)

## Future Improvements

### 4. Consider async operations for file processing
- [ ] Evaluate if PDF processing could benefit from async operations
- [ ] Consider background processing for large Excel files
- [ ] Implement progress indicators for long operations

### 5. Add type hints throughout the codebase
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