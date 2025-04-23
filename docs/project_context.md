# Backtester App - Project Context

## Purpose
This document serves as a persistent context reference for development discussions and AI assistance. It contains key information about the project's architecture, design principles, and user preferences to ensure consistency across multiple development sessions.

## Project Overview
Backtester App is an application for testing investment strategies on historical financial data, built with Python and Dash. It follows a layered architecture separating UI, application services, core logic, and data access.

## Key Architectural Principles
1. **Layered Architecture**: UI → Application → Core/Strategy/Portfolio → Data
2. **Separation of Concerns**: Components should have well-defined responsibilities
3. **Dependency Direction**: Lower layers never depend on higher layers
4. **Component Reusability**: UI and visualization components should be reusable

## Design Guidelines
1. **Modern UI**: Clean, intuitive interface with responsive design
2. **Performance**: Backtests should execute in under 30s for standard datasets
3. **Extensibility**: Easy addition of new strategies and data sources
4. **Error Handling**: Application should handle errors gracefully

## UI Aesthetics
1. **Typography**: Strictly follow 4 font sizes and 2 font weights system
2. **Spacing**: All spacing values must be divisible by 8 or 4
3. **Colors**: Follow 60/30/10 distribution (neutral/complementary/accent)
4. **Visual Structure**: Logical grouping with consistent spacing
5. **Input Fields**: Styled with dark background (`#1e222d`) and white text (`#ffffff`).
6. **Numeric Formatting**: Large numbers in specific inputs (e.g., Initial Capital) use spaces as thousand separators (client-side JS).
7. **Refer to**: [Aesthetics Guidelines](aesthetics_guidelines.md) for complete details

## Technical Stack
- **Backend**: Python 3.8+, pandas, numpy
- **Frontend**: Dash, Bootstrap, Plotly.js
- **Development**: Git, SemVer

## Language Requirements
1. **User Interface**: All UI elements must be in English
2. **Code**: All code, including comments, must be written in English
3. **Documentation**: All documentation must be maintained in English
4. **Naming Conventions**: Use English words for variables, functions, classes, and other identifiers

## User Preferences
- *This section will be updated with specific user preferences as they are expressed*

## Version Management
- The project follows SemVer (MAJOR.MINOR.PATCH)
- Version updates should be reflected in `src/version.py`
- Changes require updating the changelog and tagging in git

## Logging System
1. **Simplified Approach**: Console-based logging with standardized formatting
2. **Centralized Configuration**: Logging configuration is centralized in `app.py` and `app_factory.py`
3. **External Libraries**: External library logs are suppressed to reduce noise
4. **No File Handlers**: Removed file handlers to simplify maintenance

## Documentation References
- [Architecture Guide](architecture.md)
- [Product Design Specification](product_design_specification.md)
- [Technical Specification](technical_specification.md)
- [Aesthetics Guidelines](aesthetics_guidelines.md)

---

*Created: April 11, 2025*
*Last updated: April 23, 2025*