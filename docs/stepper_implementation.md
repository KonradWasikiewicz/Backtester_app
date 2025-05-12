# Visual Progress Indicator (Stepper) Implementation

This document outlines the implementation of the enhanced progress bar-style Stepper component that replaces the simple progress bar in the Backtester App's wizard interface.

## Overview

The Stepper component provides a visual representation of the user's progress through the wizard steps, showing:
- The current step (highlighted in blue)
- Completed steps (highlighted in green)
- Pending steps (greyed out)
- Angled dividers between segments for a modern, flowing design
- Enhanced 3D effects with gradients, shadows, and subtle highlights

The implementation allows users to navigate directly to completed steps by clicking on them, providing better context on the user's location in the wizard process. The step header backgrounds are also color-coordinated to match the stepper, making it visually clearer which step is active.

## Implementation Components

### 1. CSS Styling

The stepper component requires custom CSS styles defined in `assets/style.css`. These styles control the appearance of:
- Progress bar-style step segments with prominent angled dividers
- Status-based coloring (green for completed, blue for current, gray for pending) 
- Advanced visual effects (gradients, shadows, glows) for a modern 3D appearance
- Matching color themes for step headers and progress bar segments
- Coordinated header backgrounds that match the stepper colors
- Interactive elements (hover effects, clickable steps)

### 2. Stepper Component

The core functionality is implemented in `src/ui/components/stepper.py`, which provides:
- `create_step_indicator()` - Creates individual step segments in the progress bar
- `create_wizard_stepper()` - Assembles all segments into a complete stepper bar

### 3. Wizard Callbacks

The wizard interaction is managed in `src/ui/callbacks/wizard_callbacks.py`, which:
- Updates the stepper when navigating between steps
- Handles clicks on step indicators to navigate directly to completed steps
- Maintains synchronization between the stepper and the content being displayed

### 4. Integration with Layout

The stepper is integrated into the main wizard interface in `src/ui/layouts/strategy_config.py`, which:
- Defines step names
- Creates the initial stepper
- Positions it above the wizard content

## Interactive Features

- **Step Status Indication**: Different visual styling for completed, current, and pending steps
- **Navigation**: Clicking on completed steps navigates directly to that step
- **Progress Tracking**: Angled dividers between steps show completion progress
- **Visual Feedback**: Modern 3D appearance with color-coded segments
- **Unified Design**: Step headers match their corresponding progress bar segments 
- **Enhanced Visual Cues**: Current step has a subtle glow effect to draw attention

## Visual Design Elements

- **Angled Dividers**: Sharp angled dividers between steps create a flowing, connected appearance
- **Depth Effects**: Subtle shadows and gradients give a 3D, raised appearance to segments
- **Consistent Color Coding**: All elements use a consistent color scheme (green/blue/grey)
- **Text Enhancements**: Bold, shadowed numbers make step identification clear
- **Responsive Design**: The stepper maintains its appearance at different screen sizes

This implementation provides several advantages over the simple progress bar:
- Better visual context for the user's position in the workflow
- Direct navigation to previous steps without using "Back" buttons
- Clear indication of completed vs. pending steps
- Modern, intuitive interface that aligns with current web application design patterns

## Technical Notes

- The stepper works alongside the original progress bar for backward compatibility
- Step indicators use unique IDs that follow the pattern `step-indicator-{number}`
- Status classes (completed, current, pending) control visual appearance
- Connector lines visually link the steps to show progression
