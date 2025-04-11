# Backtester App - Aesthetics Guidelines

## General Principles

This document defines aesthetic standards for the Backtester App, ensuring a consistent and professional user interface appearance. These guidelines should be considered an integral part of the project specification.

## 1. Typography System: 4 Sizes, 2 Weights

### 1.1 Four Font Sizes
- **Size 1 (Large)**: 24px - Main headings, section titles
- **Size 2 (Medium)**: 18px - Subtitles, important information
- **Size 3 (Standard)**: 14px - Basic text, UI element labels
- **Size 4 (Small)**: 12px - Helper text, footnotes, small elements

### 1.2 Two Font Weights
- **Semi-bold (600)**: Headings, button labels, important values
- **Regular (400)**: Basic text, descriptions, standard values

### 1.3 Usage Rules
- Use the same sizes and weights consistently throughout the application
- Do not introduce additional sizes or weights without clear necessity
- Maintain visual hierarchy using these limited options

## 2. 8pt Grid System

### 2.1 Spacing Values
- **All spacing values must be divisible by 8 or 4**
- Examples:
  - Instead of 25px padding → Use 24px (divisible by 8)
  - Instead of 11px margin → Use 12px (divisible by 4)

### 2.2 Standard Spacing Values
- **Very small**: 4px
- **Small**: 8px
- **Medium**: 16px
- **Large**: 24px
- **Very large**: 32px
- **Extreme**: 48px, 64px (use sparingly)

### 2.3 Usage Rules
- Consistently apply the same spacing values to similar elements
- Maintain visual rhythm through predictable spacing
- Group related elements with the same spacing values

## 3. 60/30/10 Color Rule

### 3.1 Color Distribution
- **60%**: Neutral color (white/light gray background)
  - Main application background, cards, containers
  - Light and neutral, providing good contrast for text

- **30%**: Complementary color (dark gray/black)
  - Text, icons, subtle UI elements
  - Provides readability and contrast with background

- **10%**: Main accent color (e.g., blue)
  - Used sparingly for action buttons, highlights, indicators
  - Highlights the most important interface elements

### 3.2 Backtester App Color Palette
- **Neutral**: #F8F9FA (background), #FFFFFF (components)
- **Complementary**: #212529 (text), #495057 (helper text)
- **Accent**: #0D6EFD (main actions), #0B5ED7 (hover)

### 3.3 Chart and Visualization Colors
- **Increases/Positive**: #198754
- **Decreases/Negative**: #DC3545
- **Neutral**: #6C757D
- **Trend lines**: #0D6EFD, #6610F2, #FD7E14, #6F42C1, #20C997
- **Chart background**: #F8F9FA or #FFFFFF

### 3.4 Usage Rules
- Avoid overusing accent colors
- Maintain color consistency for similar elements and states
- Ensure sufficient contrast between text and background (min. WCAG AA)

## 4. Visual Structure

### 4.1 Grouping Principles
- **Logical Grouping**: Related elements should be visually connected
- **Intentional Spacing**: Spacing between elements should follow the grid system
- **Alignment**: Elements should be properly aligned within containers
- **Simplicity Over Decoration**: Focus on clarity and function

### 4.2 Application Layout
- Main sections should be clearly separated
- Maintain consistent margins and alignment
- Use cards to group related information
- Maintain consistent layout across different screens and sections

## 5. UI Components

### 5.1 Buttons and Interactive Elements
- **Button sizes**:
  - Standard: height 38px (padding: 8px 16px)
  - Small: height 30px (padding: 4px 8px)
- **Button states**:
  - Normal: base color
  - Hover: darker shade of base color
  - Active/Focus: even darker shade + border
  - Disabled: muted base color

### 5.2 Forms and Controls
- **Form elements**:
  - Input height: 38px
  - Internal padding: 8px 12px
  - Margin between fields: 16px
- **Labels**: Above fields, semi-bold font
- **Error messages**: Below fields, red color, small font

### 5.3 Cards and Containers
- **Internal padding**: 16px or 24px
- **Border-radius**: 4px consistently throughout the application
- **Shadows**: Subtle, uniform throughout the application
  - Standard value: `0 2px 5px rgba(0,0,0,0.1)`

## 6. Data Visualizations

### 6.1 Charts and Graphs
- **Consistent Styles**: All charts should use the same color palette
- **Axes and Grids**: Subtle, not overwhelming the data
- **Legends**: Readable, with appropriate spacing from data
- **Interactivity**: Consistent across the application (tooltips, zooms)

### 6.2 Data Tables
- **Headers**: Semi-bold font, light background distinguishing from data
- **Rows**: Alternating colors for easier reading (use very subtle contrast)
- **Cell padding**: 8px 12px
- **Text alignment**: Numbers - right, text - left, dates - center

## 7. Responsiveness

### 7.1 Breakpoints
- **Small**: < 768px
- **Medium**: 768px - 1024px
- **Large**: > 1024px

### 7.2 Layout Adaptation
- **Small screens**: Single-row layout with hamburger menu
- **Larger screens**: Side panel + main content area

## 8. Implementation Guidelines

### 8.1 CSS
- Use CSS variables for colors, spacing, and other repeating values
- Group styles by components
- Maintain consistent class naming

### 8.2 Accessibility
- Ensure sufficient text contrast (WCAG AA)
- Interactive elements must have appropriate target size (min. 44x44px)
- Support keyboard navigation

## 9. UI Consistency Checklist

Before implementing a new feature or component, check:

- [ ] Colors: Compliance with the 60/30/10 distribution rule
- [ ] Typography: Use of only the 4 specified font sizes
- [ ] Spacing: All values divisible by 8 or 4
- [ ] Structure: Elements are logically grouped with consistent spacing
- [ ] Alignment: Elements are properly aligned within containers
- [ ] Interactivity: Consistent hover, focus, active states
- [ ] Accessibility: Appropriate contrast and keyboard navigation

## 10. Language Requirements

- All user interface elements must be in English
- All code comments must be written in English
- All documentation must be maintained in English
- Variable names, function names, and other identifiers should use English words

---

*Document created: April 11, 2025*  
*Last updated: April 11, 2025*