---
allowed-tools: Bash(find:*), Bash(ls:*), Bash(tree:*), Bash(grep:*), Bash(wc:*), Bash(du:*), Bash(head:*), Bash(tail:*), Bash(cat:*), Bash(touch:*)
description: Generate comprehensive analysis and documentation of Python desktop codebase
---

# Comprehensive Python Desktop Application Analysis

## Project Discovery Phase

### Directory Structure
!`find . -type d -not -path "./.git/*" -not -path "./dist/*" -not -path "./build/*" -not -path "./__pycache__/*" -not -path "./.pytest_cache/*" -not -path "./venv/*" -not -path "./.venv/*" | sort`

### Complete File Tree
!`tree -a -I '.git|dist|build|__pycache__|*.pyc|*.pyo|*.pyd|.pytest_cache|venv|.venv|*.log' -L 4`

### File Count and Size Analysis
- Total files: !`find . -type f -not -path "./.git/*" -not -path "./__pycache__/*" -not -path "./venv/*" | wc -l`
- Python files: !`find . -name "*.py" | grep -v __pycache__ | wc -l`
- Project size: !`du -sh . --exclude=.git --exclude=__pycache__ --exclude=venv --exclude=dist --exclude=build`

## Configuration Files Analysis

### Python Package Management
- Requirements.txt: @requirements.txt
- Pyproject.toml: @pyproject.toml
- Setup.py: @setup.py
- Setup.cfg: @setup.cfg

### Python Development Tools
- Ruff config: @ruff.toml
- Ruff config alt: @.ruff.toml
- Black config: @pyproject.toml
- Pytest config: @pytest.ini
- Coverage config: @.coveragerc

### Environment & Deployment
- .env files: !`find . -name ".env*" -type f`
- PyInstaller specs: !`find . -name "*.spec"`
- Docker files: !`find . -name "Dockerfile*" -o -name "docker-compose*"`

### CI/CD Configuration
- GitHub Actions: !`find .github -name "*.yml" -o -name "*.yaml" 2>/dev/null || echo "No GitHub Actions"`

## Source Code Analysis

### Main Application Files
- Main entry point: !`find . -name "app.py" -o -name "main.py" -o -name "__main__.py" | head -5`
- Core modules: !`find ./core -name "*.py" 2>/dev/null | head -20`
- GUI modules: !`find ./gui -name "*.py" 2>/dev/null | head -20`
- Utility modules: !`find ./utils -name "*.py" 2>/dev/null | head -20`

### GUI Components (CustomTkinter/Tkinter)
- Main window: !`find . -name "*main_window*" -o -name "*mainwindow*" | grep -v __pycache__`
- Dialogs: !`find . -name "*dialog*" | grep -v __pycache__`
- Custom widgets: !`find . -name "*widget*" -o -name "*field*" | grep -v __pycache__ | head -10`

### Data Processing
- Excel handlers: !`find . -name "*excel*" | grep -v __pycache__ | head -10`
- PDF processors: !`find . -name "*pdf*" | grep -v __pycache__ | head -10`
- File parsers: !`find . -name "*parser*" -o -name "*processor*" | grep -v __pycache__ | head -10`

### Configuration & Settings
- Config files: !`find . -name "*config*" | grep -E "\.(json|ini|yaml|toml)$" | head -10`
- Settings modules: !`find . -name "*config.py" -o -name "*settings.py" | grep -v __pycache__`

### Testing Files
- Test files: !`find . -name "test_*.py" -o -name "*_test.py" | grep -v __pycache__ | head -15`
- Test fixtures: !`find . -name "conftest.py" -o -path "*/fixtures/*" | head -10`

### Documentation
- Documentation files: !`find . -name "*.md" -o -name "*.rst" -o -name "*.rtf" | head -15`

## Key Files Content Analysis

### Root Configuration Files
@README.md
@LICENSE
@.gitignore
@CLAUDE.md
@DEVELOPMENT_HISTORY.md

### Main Application Entry Point
!`find . -name "app.py" -o -name "main.py" | grep -v __pycache__ | head -1 | while read file; do echo "=== $file ==="; head -100 "$file"; echo; done`

### GUI Main Window
!`find . -name "main_window.py" | head -1 | while read file; do echo "=== $file ==="; head -100 "$file"; echo; done`

### Core Configuration
!`find . -name "config.py" | grep -v __pycache__ | head -1 | while read file; do echo "=== $file ==="; head -50 "$file"; echo; done`

## Your Task

Based on all the discovered information above, create a comprehensive analysis that includes:

## 1. Project Overview
- Application type (desktop GUI, CLI tool, library)
- Python version and major dependencies
- GUI framework (Tkinter, CustomTkinter, PyQt, etc.)
- Architecture pattern (MVC, layered, modular)

## 2. Detailed Directory Structure Analysis
For each major directory, explain:
- Purpose and role in the application
- Key Python modules and their functions
- How it connects to other parts

## 3. File-by-File Breakdown
Organize by category:
- **Main Application**: Entry points, application initialization
- **GUI Layer**: Windows, dialogs, widgets, event handlers
- **Core Logic**: Business logic, data processing, algorithms
- **Data Management**: File I/O, Excel/PDF handling, database if any
- **Configuration**: Settings management, user preferences
- **Utilities**: Helper functions, constants, common tools
- **Testing**: Test suites, fixtures, test utilities
- **Documentation**: User manuals, development docs, API docs
- **Build/Deploy**: PyInstaller specs, deployment scripts

## 4. GUI Architecture Analysis
Document:
- Main window structure and components
- Dialog flows and user interactions
- Event handling patterns
- State management approach
- Theming and styling approach

## 5. Data Flow Analysis
Explain:
- Input data sources (files, user input)
- Data processing pipeline
- Output generation (files, displays)
- Configuration and settings flow

## 6. Architecture Deep Dive
Explain:
- Overall application architecture
- Module dependencies and relationships
- Key design patterns used
- Separation of concerns

## 7. Environment & Setup Analysis
Document:
- Python version requirements
- Required packages and versions
- Installation process
- Development workflow
- Build and distribution process

## 8. Technology Stack Breakdown
List and explain:
- Python version
- GUI framework and version
- Data processing libraries (pandas, openpyxl, etc.)
- File handling libraries
- Testing frameworks
- Build and packaging tools

## 9. Visual Architecture Diagram
Create a comprehensive diagram showing:
- Application layers (GUI, Business Logic, Data)
- Component relationships
- Data flow
- File system interactions
- Module dependencies

Example structure:
```
┌─────────────────────────────────────────┐
│          GUI Layer (CustomTkinter)       │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │Main Window│  │ Dialogs  │  │Widgets ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│         Business Logic Layer             │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │PDF Handler│  │Excel Mgr │  │Parser  ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│           Data Layer                     │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │File I/O  │  │Config    │  │Cache   ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
```

## 10. Key Insights & Recommendations
Provide:
- Code quality assessment
- GUI/UX considerations
- Performance optimization opportunities
- Potential improvements
- Security considerations (file access, data handling)
- Maintainability suggestions
- Distribution and deployment recommendations

Think deeply about the desktop application structure and provide comprehensive insights that would be valuable for maintaining and extending the application.

At the end, write all of the output into a file called "codebase_analysis.md"