# TODO List - DJs Timeline-maskin

## Current Bugs

### ~~Multi-Resolution Window Scaling Issues (v2.6.14)~~ — RESOLVED
- Fixed by subsequent layout changes (v2.7.x series)

### ~~PDF rename/move while file is open externally (macOS)~~ — RESOLVED
- [x] **B1**: ~~Detect open PDF files before rename/move~~ — Fixed in v2.7.9

---

## Security & Stability Fixes

### Critical (fix first)

- [x] **C1**: ~~Remove dead `add_row` method from `excel_manager.py`~~ — Fixed in v2.7.3
- [x] **C2**: ~~Add max retry count to `while True` loops~~ — Fixed in v2.7.3
- [x] **C3**: ~~Make `config.py:save_config` atomic~~ — Fixed in v2.7.3

### High

- [x] **H1**: ~~Fix `add_row_with_xlsxwriter` return type~~ — Now raises PermissionError. Fixed in v2.7.6
- [x] **H2**: ~~Add path traversal protection to `template_manager.py`~~ — `_safe_template_path()` on all ops. Fixed in v2.7.6
- [x] **H3**: ~~Fix widget-after-destruction race in `update_dialog.py`~~ — `winfo_exists()` guard added. Fixed in v2.7.6
- [x] **H4**: ~~Fix unbound `result` variable in update check thread~~ — Initialized `result = None`. Fixed in v2.7.6
- [x] **H5**: ~~Fix `ScrollableText.__getattr__` infinite recursion~~ — Uses `object.__getattribute__`. Fixed in v2.7.6
- [x] **H6**: ~~Replace `bind_all("<MouseWheel>")` with widget-specific bindings~~ — Fixed in v2.7.6
- [x] **H7**: ~~Validate GitHub URL before `webbrowser.open()`~~ — HTTPS + github.com check. Fixed in v2.7.6

### Medium

- [x] **M1**: ~~Add `--` separator before paths in subprocess calls~~ — Fixed in v2.7.7
- [x] **M2**: ~~Check Content-Length before downloading full response in version checker~~ — Fixed in v2.7.7
- [x] **M3**: ~~Replace hardcoded Swedish column names with dynamic field display names~~ — Fixed in v2.7.7
- [x] **M4**: ~~Close workbook on reload in ExcelManager~~ — Fixed in v2.7.7
- [x] **M5**: ~~Close read_workbook in add_row_with_xlsxwriter~~ — Fixed in v2.7.7
- [x] **M6**: ~~Always attempt os.replace for temp file~~ — Fixed in v2.7.7
- [x] **M7**: ~~Fix backup_path NameError on new template~~ — Fixed in v2.7.7
- [x] **M8**: ~~Make template writes atomic~~ — Fixed in v2.7.7
- [x] **M9**: ~~Fix string-based version comparison in config migration~~ — Fixed in v2.7.7
- [x] **M10**: ~~Fix load-modify-save race condition with threading lock~~ — Fixed in v2.7.7
- [x] **M11**: ~~Remove call to nonexistent update_filename_preview method~~ — Fixed in v2.7.7
- [x] **M12**: ~~Clear undo stacks when fields are recreated~~ — Fixed in v2.7.7
- [x] **M13**: ~~Clear undo_widgets list on field recreation~~ — Fixed in v2.7.7
- [x] **M14**: ~~Cancel scheduled after() callbacks on dialog close~~ — Fixed in v2.7.7
- [x] **M15**: ~~Replace all DEBUG print/logger.info with logger.debug()~~ — Fixed in v2.7.7

### Low (cleanup)

- [x] **L1**: ~~Remove unused SSL context method~~ — Fixed in v2.7.8
- [x] **L2**: ~~Add type validation for `skip_versions` from config~~ — Fixed in v2.7.8
- [x] **L3**: ~~Guard `ctypes.windll` with `platform.system() == 'Windows'` check~~ — Fixed in v2.7.8
- [x] **L4**: ~~Fix `clean_pdf_text` returning `None` instead of `""`~~ — Fixed in v2.7.8
- [x] **L5**: ~~Fix `.pdf` removal from all positions in filename~~ — Fixed in v2.7.8
- [x] **L6**: ~~Clamp tooltip positions to screen bounds~~ — Fixed in v2.7.8
- [x] **L7**: ~~Remove unreachable code after return statements~~ — Fixed in v2.7.8

---

## GUI Improvements

- [x] ~~**G1**: Shorten "Kopiera ned filnamnet till Excelfältet" button text (e.g., "Kopiera till Excel" or icon + tooltip)~~ — Fixed in v2.8.3
- [x] ~~**G3**: Differentiate "Rensa utan spara" button visually from "Spara allt och rensa" (muted/outlined style)~~ — Fixed in v2.8.3
- [x] ~~**G4**: Add visible selection indicator on active row color button~~ — Fixed in v2.8.3
- [x] ~~**G5**: Improve formatting toolbar button discoverability (larger targets, tooltips)~~ — Fixed in v2.8.3
- [x] ~~**G6**: Add "Open folder" button near file list — opens the selected PDF folder in Finder so user can see its contents without searching for it~~ — Fixed in v2.8.2

---

## Feature Ideas

- [x] ~~**F1**: Search/filter box in PDF file list~~ — Fixed in v2.8.0
- [ ] **F2**: Keyboard shortcuts for common actions (Save+Clear, Next/Previous PDF)
- [ ] **F3**: Auto-advance to next PDF in file list after "Spara allt och rensa"
- [ ] **F4**: Drag-and-drop PDF files onto app window
- [x] ~~**F5**: File list sorting options (name, date modified, size)~~ — Fixed in v2.8.0
- [ ] **F6**: Recently used Excel files dropdown
- [ ] **F7**: Batch progress indicator ("Behandlad: 12/381")
- [ ] **F8**: Undo last added Excel row
- [ ] **F9**: Zoom in/out on PDF preview (Cmd+Mousewheel and +/- buttons)
- [ ] **F10**: Delete single files from the file list
- [x] ~~**F11**: Fix undo/redo in text widgets~~ — Fixed in v2.7.5 (single custom snapshot-based system)

---

## Pending Testing

### Unit Tests for Individual Mixins
**Implementation Strategy**: Mostly autonomous unit tests for mixin functionality
- [ ] Test PDF Operations Mixin - file selection logic, validation, renaming
- [ ] Test Excel Operations Mixin - row creation, column mapping
- [ ] Test Event Handlers - event processing logic (mocked GUI interactions)
- [ ] Test Undo/Redo - snapshot-based system (debounce timers, paste/cut/format saves)

### Phase 3 Manual Verification Tests
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

---

## Future Improvements

### Consider async operations for file processing
- [ ] Evaluate if PDF processing could benefit from async operations
- [ ] Consider background processing for large Excel files
- [ ] Implement progress indicators for long operations

### Field Configuration Dialog Enhancements
**Still Pending**:
- [ ] Add "Återställ till standard" (Restore to default names) button - clears all custom name fields

### Add type hints throughout the codebase
- [ ] Add type hints to all function signatures
- [ ] Add type hints for class attributes
- [ ] Use typing module for complex types
- [ ] Consider using mypy for type checking

---

## Recently Completed ✅

### ✅ Fix Formatted Text Lost in Excel (v2.8.1) - COMPLETE
- ✅ Fixed CellRichText class name check (`'RichText'` → `'CellRichText'`) in excel_operations.py
- ✅ Made clean_pdf_text defensive for non-string truthy objects (v2.7.8 L4 regression)

### ✅ Search/Filter and Sorting in PDF File List (v2.8.0) - COMPLETE
- ✅ F1: Real-time search with clear button, filtered count display
- ✅ F5: Sort by name (A-Ö/Ö-A), date (newest/oldest), size (largest/smallest)
- ✅ Sort preference persisted in config

### ✅ Low-Priority Cleanup Fixes (v2.7.8) - COMPLETE
- ✅ L1-L7: All 7 low-priority issues fixed (unused SSL method, skip_versions type validation, Windows DPI guard, clean_pdf_text None fix, .pdf suffix removal, tooltip clamping, dead code removal)

### ✅ Medium-Priority Security/Stability Fixes (v2.7.7) - COMPLETE
- ✅ M1-M15: All 15 medium-priority issues fixed (flag injection, resource leaks, race conditions, version comparison, atomic writes, debug logging)

### ✅ Fix Undo/Redo for Text Widgets (v2.7.5) - COMPLETE
- ✅ Replaced dual undo system with single snapshot-based custom undo
- ✅ Debounced typing snapshots (500ms), phrase-level undo, formatting preserved through cycles
- ✅ Tk built-in undo disabled, synchronous state saves, 3-second max interval

### ✅ Critical Security/Stability Fixes (v2.7.3) - COMPLETE
- ✅ C1: Removed dead `add_row` method from excel_manager.py
- ✅ C2: Added max retry count to `while True` loops
- ✅ C3: Made config save atomic with temp file + os.replace()

### ✅ PDF Preview Panel & File List (v2.7.0-v2.7.1) - COMPLETE
- ✅ Full-height PDF preview panel with file list
- ✅ Auto-move PDFs, improved tooltips, layout improvements

### ✅ Build Tools & Installer Configuration (v2.6.17) - COMPLETE
- ✅ PyInstaller spec, Inno Setup installer, GitHub URLs, dependency handling

### ✅ GitHub Version Checking System (v2.6.17) - COMPLETE
- ✅ Secure GitHub API integration, Swedish UI, version skipping, privacy-first design

### ✅ Template Save Visual Feedback Bug Fix (v2.6.13) - COMPLETE
- ✅ Non-blocking flash effect replaced modal dialog for template save feedback

*(For detailed development history, see docs/DEVELOPMENT_HISTORY.md)*
