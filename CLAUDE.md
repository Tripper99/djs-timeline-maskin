# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python desktop application called "DJs Timeline-maskin" (DJs Timeline Machine). It is designed to help investigative journalists and researchers to quickly renaming pdf files and/or create timelines i excel. The first part of the app processes PDF files extracts different parts of the filename. User can then edit these parts and rename the file. It is also possible to copy the old or new file name to the second part of the app: The excel integration. Here the user can add information to a number of fields. By cklicking a button user can then both rename the pdf-file and add a row to a selected excel-document. 
A third way to use the app is by manually add content to excel-fields and create a new excel row without any pdf file selected or renamed. This is practical for researchers whon for example is picking information from books or other sources. 
The application has been refactored from a single large file into a modular structure.

## Current Status (v2.2.1)

**Project Documentation Update**:
- Comprehensive codebase analysis completed and documented in `codebase_analysis.md`
- TODO list created with prioritized improvement tasks in `TODO.md`
- Claude Code command files added for automated analysis and documentation updates

**Major Layout Improvements (v2.2.0)**:
- Fixed persistent gap above Händelse field that resisted multiple fix attempts
- Achieved proper 40/30/30 column distribution in Excel integration section
- Implemented resizable column handles using tk.PanedWindow for better large monitor support
- Date/time fields moved to top of left column for easy access
- UI made significantly more compact with reduced padding throughout

**Key Technical Solutions**:
- Gap issue: Fixed by correcting row weight distribution (giving weight to text widget row instead of header row)
- Column proportions: Restructured layout to move date/time fields from complex nested subframe to left column
- Resizable handles: Native tk.PanedWindow with minimum width constraints (300px left, 200px middle/right)

**Testing Notes**:
- Always run Ruff syntax check before committing
- Test application startup after layout changes
- ttk.PanedWindow does not support minsize parameter - use tk.PanedWindow instead

## Additional guideline on github commit
**Never* mention yourself (Claude) in comment when doing commit. *Never* write stuff like "🤖 Generated with [Claude Code](https://claude.ai/code) Co-Authored-By: Claude <noreply@anthropic.com>". 

## Working Principles

- **Honest Collaboration Guideline**: 
  * Prioritize technical accuracy. Point out bugs, inefficiencies, and better approaches immediately. 
  * Confirm understanding with minimal acknowledgment. Focus on code quality, performance, and maintainability. 
  * Challenge bad ideas with specific alternatives.
  
  [... rest of the existing content remains unchanged ...]