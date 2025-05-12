import dash_bootstrap_components as dbc
from dash import html
import logging

# Import centralized IDs
from src.ui.ids.ids import WizardIDs

logger = logging.getLogger(__name__)

def create_step_indicator(step_number, label, status="pending", is_clickable=True):
    """
    Creates a single step indicator for the progress bar-like stepper component.
    
    Args:
        step_number (int): The number of the step
        label (str): The label for the step
        status (str): The status of the step - 'completed', 'current', or 'pending'
        is_clickable (bool): Whether the step should be clickable
    
    Returns:
        html.Div: The step indicator component
    """
    # Define class based on status
    base_class = "step-indicator"
    status_class = f"{base_class} {status}"
    if is_clickable:
        status_class += " clickable"
    
    # Create a progress-bar segment style step indicator
    return html.Div([
        html.Div(
            html.Span(str(step_number), className="step-number"),
            className="step-segment"
        ),
        html.Span(label, className="step-label d-none d-lg-block") # Hide on small screens
    ], className=status_class, id=WizardIDs.step_indicator(step_number))

def create_wizard_stepper(current_step_index, step_names):
    """
    Creates a wizard stepper component showing the progress through the wizard steps.
    This creates a progress-bar-like stepper instead of individual circle indicators.
    
    Args:
        current_step_index (int): The index of the current step (0-based)
        step_names (list): List of step names
    
    Returns:
        html.Div: The stepper component
    """
    logger.debug(f"Creating wizard stepper with current step index: {current_step_index}")
    
    step_indicators = []
    
    # Create indicators for each step
    for i, name in enumerate(step_names):
        # Determine step status
        status = "pending"
        if i < current_step_index:
            status = "completed"
        elif i == current_step_index:
            status = "current"
        
        # Determine if clickable (only completed steps and current step + 1)
        is_clickable = (i <= current_step_index + 1) and (i != current_step_index)
        
        # Create the step indicator
        step_indicator = create_step_indicator(
            step_number=i + 1,  # 1-based step number for display
            label=name,
            status=status,
            is_clickable=is_clickable
        )
        
        # Add to stepper container (no separate connector lines in the new design)
        step_indicators.append(step_indicator)
    
    return html.Div(step_indicators, className="wizard-stepper progress-style mb-4", id=WizardIDs.WIZARD_STEPPER)
