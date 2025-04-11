# Backtester App - Workflow Guide

This guide explains how to maintain consistency in development by following the documentation rules and utilizing the automatic versioning system.

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

## Automatic Versioning

The project includes an automatic versioning system that follows Semantic Versioning (MAJOR.MINOR.PATCH). The system can automatically update versions based on commit messages.

### Setting Up Automatic Versioning

To enable automatic versioning with git hooks:

```bash
python scripts/auto_version.py setup
```

This will create a pre-commit hook that automatically updates the version based on commit messages.

### How Version Detection Works

The version update type is determined by keywords in your commit messages:

- **Major version** (breaking changes): Include "breaking", "major change", or "major update" in commit message
- **Minor version** (new features): Include "new feature", "minor change", or "minor update" in commit message
- **Patch version** (bug fixes): Default for all other commits

### Manual Version Updates

You can also manually update versions:

```bash
python scripts/auto_version.py patch  # Increment patch version (0.0.X)
python scripts/auto_version.py minor  # Increment minor version (0.X.0)
python scripts/auto_version.py major  # Increment major version (X.0.0)
```

### Version Tracking

Each version update will:
1. Update the version number in `src/version.py`
2. Update the `CHANGELOG.md` file with commit messages
3. Add both files to git staging

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

---

*Document created: April 11, 2025*  
*Last updated: April 11, 2025*