# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python desktop application called "DJs Timeline-maskin" (DJs Timeline Machine). It is designed to help investigative journalists and researchers to quickly renaming pdf files and/or create timelines i excel. The first part of the app processes PDF files extracts different parts of the filename. User can then edit these parts and rename the file. It is also possible to copy the old or new file name to the second part of the app: The excel integration. Here the user can add information to a number of fields. By cklicking a button user can then both rename the pdf-file and add a row to a selected excel-document. 
A third way to use the app is by manually add content to excel-fields and create a new excel row without any pdf file selected or renamed. This is practical for researchers whon for example is picking information from books or other sources. 
The application has been refactored from a single large file into a modular structure.

## Current Status (v2.8.8)

**Latest Status (v2.8.8)**: Auto-refresh file list and select next file after "Spara allt och rensa" — after processing a PDF, the file list refreshes automatically, selects the next file at the same index, loads its preview and fields, and shows "Inga fler PDF-filer i mappen." when the folder is empty.

**Key Features**:
- **Single Custom Undo System**: Tk built-in undo disabled; snapshot-based undo with debounced typing (500ms), immediate saves before destructive ops, 3-second max interval between snapshots
- **GitHub Version Checking**: Secure update checking via "Verktyg → Sök efter uppdateringar..." with Swedish interface, version skipping, and browser-based downloads
- **Direct Template Saving**: "Spara mall" button saves directly to active template, "Spara mall som..." saves to new file
- **Intelligent Button States**: Dynamic enabling/disabling based on template type and modification status
- **Template Validation**: "Standard" template protected from direct overwrites, custom templates fully supported
- **Race Condition Prevention**: Comprehensive protection during template loading and state transitions
- **Field Configuration System**: Custom field names and visibility states with template support
- **Excel Integration**: Disabled fields automatically excluded from Excel operations
- **PDF File List**: Search/filter with real-time matching, sort by name/date/size, persisted sort preference, open folder in Finder, delete file to Trash
- **Recently Used Dropdowns**: Quick-switch dropdowns for Excel files and output folders (max 10, persisted)

**Architecture Status**:
- **Modular Design**: Clean architecture with main_window.py reduced from 35,000+ tokens to 384 lines
- **Undo System**: Single custom snapshot-based undo in `gui/undo_manager.py` — Tk undo disabled, debounce timers for typing, synchronous state saves for paste/cut/format
- **Field State System**: Complete transition from "hidden" to "disabled" terminology
- **Visual Styling**: Centralized field styling system (gui/field_styling.py) for consistent disabled field appearance

**Testing Framework**:
- Comprehensive test suite available: `python -m pytest tests/ -v`
- Always run Ruff syntax check before committing: `ruff check . --fix`
- Integration tests: `python -m pytest tests/test_integration_workflows.py -v -s`
- See TESTING_GUIDE.md for complete workflow procedures
- **Update Check Testing**: Test GitHub version checking via "Verktyg → Sök efter uppdateringar..." menu

## Documentation Management Guidelines

**CLAUDE.md Content Strategy**:
- Keep CLAUDE.md focused on current status and working principles only
- Include only the very latest development achievement (current version) in Current Status section
- Remove older development history when adding new entries to prevent document growth
- For detailed development history, technical analysis, and version milestones → use `docs\DEVELOPMENT_HISTORY.md`
- Always reference DEVELOPMENT_HISTORY.md for comprehensive historical details
- Maintain clean, actionable guidance rather than extensive historical records

**Development History Documentation**:
- Comprehensive technical details, root cause analyses, and implementation insights go in `docs\DEVELOPMENT_HISTORY.md`
- Each major version should have detailed entry with problem/solution/technical excellence documentation
- Include investigation methodology, sub-agent usage, and development process insights
- Preserve valuable technical knowledge for future development sessions

## Additional guideline on github commit
**Never* mention yourself (Claude) in comment when doing commit. *Never* write stuff like "🤖 Generated with [Claude Code](https://claude.ai/code) Co-Authored-By: Claude <noreply@anthropic.com>". 

## Working Principles

- **Honest Collaboration Guideline**: 
  * Prioritize technical accuracy. Point out bugs, inefficiencies, and better approaches immediately. 
  * Confirm understanding with minimal acknowledgment. Focus on code quality, performance, and maintainability. 
  * Challenge bad ideas with specific alternatives.

- **UX Validation & Bug Investigation Approach** (learned in v2.2.15):
  * Use specialized sub-agents (bug-finder-debugger) for systematic investigation of behavioral issues
  * Always compare working vs non-working patterns to identify root cause differences
  * Focus on user experience consistency - fields of same type should behave identically
  * Distinguish between data validation (necessary) and UX validation (can be overly aggressive)
  * Document specific code locations and event bindings when investigating GUI behavior issues
  * Test behavioral changes thoroughly to ensure consistent UX across similar UI elements

- **Systematic Feature Implementation Approach** (learned in v2.3.0):
  * Use complete rewrite architecture with GitHub fallback safety for major features
  * Separate identity systems (internal IDs vs display names) for flexibility and maintainability  
  * Create comprehensive validation frameworks with real-time feedback and visual indicators
  * Design professional configuration interfaces with clear protected/modifiable sections
  * Implement complete reset mechanisms with warning dialogs for data-destructive operations
  * Always identify and document any remaining bugs with specific fix plans for next session
  * Use specialized sub-agents (architecture-planner, code-writer) for systematic implementation phases

- **Don't make code backward compatible unless specifically asked for**
  * This is a new project. Backward compatibility is not needed. 

- **Critical Bug Investigation Methodology** (learned in v2.3.3 & v2.5.1):
  * Use multiple specialized subagents (bug-finder-debugger, architecture-planner, code-reviewer-refactorer) for systematic root cause analysis
  * Trace complete data flow from configuration → storage → usage to identify exact failure points
  * Search for architectural inconsistencies - look for pattern violations (e.g., 9 methods use correct approach, 1 uses wrong approach)
  * Add comprehensive debug logging at every critical data transition point
  * Verify fixes work for all edge cases and don't cause regression in existing functionality
  * Use systematic investigation with sub-agents rather than assumptions - they often reveal deeper architectural insights
  * Document exact sequence of events and technical solutions for future reference

- **Major UI/UX Transformation Methodology** (learned in v2.5.2):
  * Break complex transformations into distinct phases with clear deliverables and testing milestones
  * Use specialized sub-agents extensively for architecture planning, code generation, and validation
  * Maintain comprehensive backward compatibility through alias systems during terminology transitions
  * Create centralized systems (like field styling) to ensure consistency across large codebases
  * Always verify that core business logic (Excel operations) remains unchanged during UI transformations
  * Test systematically after each phase rather than at the end - complex changes require incremental validation
  * Document phase completion and commit incremental progress to enable rollback if needed

- **Template Loading Race Condition Prevention** (learned in v2.6.3-v2.6.5):
  * Use timeout-based protection systems to prevent event interference during critical state transitions
  * Implement comprehensive logging with clear visual indicators for debugging complex GUI state issues
  * Add protection flags during template loading to prevent field change events from causing race conditions
  * Use scheduled callbacks with adequate timeout periods (150ms) for robust event isolation
  * Debug template state issues systematically with detailed logging at every critical transition point
  * Test template loading operations thoroughly across different timing scenarios and user interactions

- **Complex Layout Investigation Methodology** (learned in v2.6.10):
  * Use multiple specialized sub-agents (architecture-planner, bug-finder-debugger, code-writer) for comprehensive technical investigation
  * Document failed approaches as thoroughly as successful ones to prevent repeated futile attempts
  * Recognize when issues may require fundamental architecture changes rather than incremental fixes
  * Professional handling of unresolved technical challenges with complete documentation for future investigation
  * Some CustomTkinter layout behaviors may be non-obvious and require community consultation or alternative approaches
  * Systematic investigation methodology valuable even when resolution is not achieved

- **Failed Complex Implementation Risk Management** (learned in v2.6.15):
  * Comprehensive multi-component changes carry high risk of making problems worse
  * Excellent technical analysis doesn't guarantee successful implementation
  * Always implement incrementally with user validation at each step
  * Over-engineering can disrupt working functionality even when addressing real issues
  * User feedback is critical - technical correctness insufficient for complex UI changes
  * When implementing fails badly, clean revert is better than attempting fixes on broken foundation
  * Future scaling solutions should focus on minimal targeted changes rather than architectural overhauls

- **Multi-Agent Security-Focused Development** (learned in v2.6.17):
  * Use specialized sub-agents (architecture-planner, security-auditor) for comprehensive feature planning
  * Security audit before implementation prevents vulnerabilities and guides secure design patterns
  * Incremental implementation with progress tracking ensures quality and allows course correction
  * Swedish localization from the start improves user experience significantly
  * Privacy-first design principles (features disabled by default) build user trust
  * Comprehensive error handling with localized messages improves user confidence
  * Browser-based download approach avoids security risks of in-app update mechanisms

- **mandatory git commit routine**
  * Before writing code you should always make a new version and commit it to git with comments on what you are about to do. 
  * After making changes the user must get an oportunity to do testruns. 
  * If and when user says that changes works, you should do a new commit, with comments reflecting the successful code change. 
  * Never write comments about successful revisions unless the user has done test runs. 
- When presenting a plan for code change always start the plan with saving of new version and git commit. The reason for this is that user can't approav plan if he is not sure that you will remember the backup procedure.
- When saving a new version of project never use the old version number (e.g v2.5.11) with added text like "fix" och with an added explanation of what was done (e.g "v2.5.11-template-readability". **Always** use a new version number. Information about what changes has been done (or what changes that are planned to be done) should be added as comment to the git commit.