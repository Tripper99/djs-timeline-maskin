# TODO List - DJs Timeline-maskin

## Current Bugs

### ~~Multi-Resolution Window Scaling Issues (v2.6.14)~~ — RESOLVED
- Fixed by subsequent layout changes (v2.7.x series)

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

- [ ] **M1**: Add `--` separator before paths in `subprocess.run(["open", path])` calls — prevent filenames starting with `-` being interpreted as flags
- [ ] **M2**: Use streaming or check `Content-Length` before downloading full response in version checker (`checker.py:133`)
- [ ] **M3**: Fix hardcoded Swedish column names in `_prepare_special_data` (`excel_manager.py:491,515,525`) — use `_get_field_display_name()` instead
- [ ] **M4**: Add proper workbook `close()` to `ExcelManager` — resource leak (`excel_manager.py:36`)
- [ ] **M5**: Close `read_workbook` in `add_row_with_xlsxwriter` — resource leak (`excel_manager.py:298`)
- [ ] **M6**: Fix temp file orphan when original Excel deleted (`excel_manager.py:473`) — always attempt `os.replace()`
- [ ] **M7**: Fix `backup_path` NameError when template save fails on new template (`template_manager.py:176`)
- [ ] **M8**: Make template writes atomic — write to temp + `os.replace()` (`template_manager.py:170`)
- [ ] **M9**: Fix string-based version comparison in config migration — will break at v2.10+ (`config.py:331-367`)
- [ ] **M10**: Fix load-modify-save race condition across config methods (`config.py:125+`)
- [ ] **M11**: Fix missing `update_filename_preview` method — crash when applying field config (`main_window.py:641`)
- [ ] **M12**: Clear undo stacks when fields are recreated — memory leak with stale widget IDs (`undo_manager.py`)
- [ ] **M13**: Clear `undo_widgets` list on field recreation — leaks references to destroyed widgets (`undo_manager.py:414`)
- [ ] **M14**: Cancel scheduled `after` callbacks when dialogs close (`field_config_dialog.py:1255`, `pdf_preview.py:214`)
- [ ] **M15**: Replace all `print("DEBUG: ...")` and `logger.info("DEBUG: ...")` with `logger.debug()` across codebase

### Low (cleanup)

- [ ] **L1**: Remove unused SSL context method (`validator.py:245`)
- [ ] **L2**: Add type validation for `skip_versions` from config (`config.py:276`)
- [ ] **L3**: Guard `ctypes.windll` with `platform.system() == 'Windows'` check (`main_window.py:148`)
- [ ] **L4**: Fix `clean_pdf_text` returning `None` instead of `""` (`filename_parser.py:109`)
- [ ] **L5**: Fix `.pdf` removal from all positions in filename (`filename_parser.py:19`)
- [ ] **L6**: Clamp tooltip positions to screen bounds (`utils.py:26`)
- [ ] **L7**: Remove unreachable code after return statements (`excel_fields.py:769`)

---

## GUI Improvements

- [ ] **G1**: Shorten "Kopiera ned filnamnet till Excelfältet" button text (e.g., "Kopiera till Excel" or icon + tooltip)
- [ ] **G2**: Consider 2-column layout for date/time pairs (Startdatum+Starttid on same row) to save vertical space
- [ ] **G3**: Differentiate "Rensa utan spara" button visually from "Spara allt och rensa" (muted/outlined style)
- [ ] **G4**: Add visible selection indicator on active row color button
- [ ] **G5**: Improve formatting toolbar button discoverability (larger targets, tooltips)

---

## Feature Ideas

- [ ] **F1**: Search/filter box in PDF file list (biggest workflow win for large file sets)
- [ ] **F2**: Keyboard shortcuts for common actions (Save+Clear, Next/Previous PDF)
- [ ] **F3**: Auto-advance to next PDF in file list after "Spara allt och rensa"
- [ ] **F4**: Drag-and-drop PDF files onto app window
- [ ] **F5**: File list sorting options (name, date modified, size)
- [ ] **F6**: Recently used Excel files dropdown
- [ ] **F7**: Batch progress indicator ("Behandlad: 12/381")
- [ ] **F8**: Undo last added Excel row
- [x] **F9**: ~~Fix undo/redo in text widgets~~ — Fixed in v2.7.5 (single custom snapshot-based system)

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
