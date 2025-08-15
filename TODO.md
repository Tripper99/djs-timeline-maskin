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

### 2. Update requirements.txt to include all dependencies
- [ ] Add xlsxwriter (currently missing)
- [ ] Add customtkinter (currently missing)
- [ ] Verify all other dependencies are listed with correct versions

## Medium Priority - Testing & Documentation

### 3. Expand testing beyond layout tests
- [ ] Add unit tests for core modules:
  - [ ] Test filename_parser.py
  - [ ] Test pdf_processor.py
  - [ ] Test excel_manager.py
  - [ ] Test config.py
- [ ] Add integration tests for main workflows
- [ ] Add GUI tests for critical user interactions

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