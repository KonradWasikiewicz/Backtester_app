# Backtester App - Workflow Guide

This guide explains how to maintain consistency in development by following the documentation rules and utilizing the version management system.

## Starting New Development Conversations

To ensure that all development conversations maintain the proper context and follow established guidelines, follow these steps at the beginning of any new conversation:

1. **Load the project context**:
   ```bash
   python scripts/load_context.py
   ```
   This will output the essential context from your project documentation. Copy this output and include it at the beginning of your conversation to provide the AI with necessary context.

2. **Reference specific documentation** when needed:
   - For architectural questions: refer to `docs/architecture.md`
   - For UI design and aesthetics: refer to `docs/aesthetics_guidelines.md`
   - For product specifications: refer to `docs/product_design_specification.md`
   - For technical implementation: refer to `docs/technical_specification.md`

3. **Update context with new preferences** when you make important decisions:
   ```bash
   python scripts/context_manager.py update_preferences "Your new preference here"
   ```

## Version Management

The project uses a unified version management system that follows Semantic Versioning (MAJOR.MINOR.PATCH). All version management tasks can be performed using the single `version_manager.py` script.

### Version Management Commands

```bash
# Display current version information
python scripts/version_manager.py info

# Update version numbers
python scripts/version_manager.py update [major|minor|patch] --changes "Change description"

# Create a git tag for the current version
python scripts/version_manager.py tag [--push]

# Set up automated versioning with git hooks
python scripts/version_manager.py setup-hooks

# List available versions
python scripts/version_manager.py restore --list

# Restore to a specific version
python scripts/version_manager.py restore [--version v1.0.0] [--force]
```

### Automatic Versioning

After setting up git hooks with `python scripts/version_manager.py setup-hooks`, version numbers will be automatically updated based on your commit messages:

- **Major version** (breaking changes): Include "breaking", "major change", or "major update" in commit message
- **Minor version** (new features): Include "new feature", "minor change", or "minor update" in commit message
- **Patch version** (bug fixes): Default for all other commits

### Version Workflow Example

A typical workflow for a new feature would be:

1. Make your code changes
2. Test thoroughly
3. Commit your changes with a descriptive message (e.g., "new feature: added strategy optimization")
4. The version will be automatically updated if git hooks are set up
5. Tag the version: `python scripts/version_manager.py tag --push`

## Language and Formatting Requirements

All development must follow these language requirements:

1. **English Only**: All code, comments, documentation, and UI elements must be in English
2. **Consistent Naming**: Use English words for all variables, functions, and classes
3. **Documentation Format**: Follow existing documentation format and structure

## UI Development Guidelines

When making UI changes:

1. Check the aesthetics guidelines in `docs/aesthetics_guidelines.md`
2. Verify spacing values are divisible by 8 or 4
3. Adhere to the color distribution rule (60/30/10)
4. Use only the 4 specified font sizes and 2 font weights
5. Ensure proper component grouping and alignment

## Ensuring Consistency

Before submitting changes:

1. Validate that changes align with architectural principles
2. Verify UI components follow aesthetic guidelines
3. Run the UI consistency checklist from the aesthetics document
4. Ensure all code and comments are in English
5. Commit with descriptive messages that appropriately indicate version bump type
*Last updated: April 24, 2025*