# TODO List - DJs Timeline-maskin

## Current Bugs

### 1. Template Name Display State Reset Bug ✅ **RESOLVED**
**Problem**: Template name background color doesn't reset to orange after load template operations
**Status**: 
- ✅ **"Spara mall..." (Save template)**: Background correctly resets from red to orange after successful save
- ✅ **"Ladda mall..." (Load template)**: Background correctly resets and shows proper state

### 2. Template State Display Bug - Reset to Standard ✅ **RESOLVED** (v2.6.6)
**Area**: Excel custom names config dialog window
**Problem**: "Återställ till standard" button didn't update template name display
**Resolution**: Fixed in v2.6.6 by adding proper template state management to `_reset_to_defaults` method
**Fix Details**: 
- Added `self.current_template = "Standard"` to reset template name
- Added `self.is_template_modified = False` to clear modified state
- Added `self._update_template_name_display()` to update visual indicator
**Verification**: User confirmed fix works correctly - template name now properly shows "Aktuell mall: Standard" with orange background after reset

## Pending Testing

### 3. Unit Tests for Individual Mixins
**Implementation Strategy**: Mostly autonomous unit tests for mixin functionality
- [ ] Test PDF Operations Mixin - file selection logic, validation, renaming
- [ ] Test Excel Operations Mixin - row creation, column mapping
- [ ] Test Event Handlers - event processing logic (mocked GUI interactions)
- [ ] Test Undo/Redo - command pattern implementation

### 4. Phase 3 Manual Verification Tests
**Implementation Strategy**: User active participation required
- [ ] **Visual/Layout Testing**:
  - [ ] Column resizing functionality
  - [ ] Field focus behaviors and highlighting
  - [ ] Dialog positioning and appearance
  - [ ] Theme and styling verification
- [ ] **Error Scenario Testing**:
  - [ ] Corrupted PDF handling
  - [ ] Locked Excel file scenarios
  - [ ] Invalid configuration recovery

## Future Improvements

### 5. Consider async operations for file processing
- [ ] Evaluate if PDF processing could benefit from async operations
- [ ] Consider background processing for large Excel files
- [ ] Implement progress indicators for long operations

### 6. Field Configuration Dialog Enhancements
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

### 7. Add type hints throughout the codebase
- [ ] Add type hints to all function signatures
- [ ] Add type hints for class attributes
- [ ] Use typing module for complex types
- [ ] Consider using mypy for type checking