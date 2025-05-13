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

def create_wizard_stepper(current_step_index, completed_steps=None):
    """
    Creates a list of step indicator components for the wizard stepper.
    
    Args:
        current_step_index (int): The index of the current step (1-based)
        completed_steps (set, optional): Set of step indices that have been completed/confirmed
    
    Returns:
        list: A list of html.Div components representing the step indicators.
    """
    logger.debug(f"Creating wizard stepper indicators with current step index: {current_step_index}, completed steps: {completed_steps}")
    
    # Initialize completed_steps if not provided
    if completed_steps is None:
        completed_steps = set()
      # Define step names
    step_names = [
        "Strategy",
        "Date Range",
        "Tickers",
        "Management", # Shortened from "Risk Management" for brevity if needed
        "Costs",
        "Rebalancing",
        "Summary"
    ]
    
    step_indicators = []
      # Create indicators for each step
    for i, name in enumerate(step_names):
        # Determine step status (1-based indexing)
        step_num = i + 1
        status = "pending"
        if step_num in completed_steps:
            status = "completed"
        elif step_num == current_step_index:
            status = "current"
        
        # Determine if clickable (only completed steps and current step + 1)
        # Or allow clicking current step to 'refresh' or if logic changes
        is_clickable = (step_num in completed_steps or step_num == current_step_index + 1 or step_num == current_step_index) and (step_num <= len(step_names))

        # Create the step indicator
        step_indicator = create_step_indicator(
            step_number=step_num,  # 1-based step number for display
            label=name,
            status=status,
            is_clickable=is_clickable # Pass clickability
        )
        
        step_indicators.append(step_indicator)
    
    # Return the list of indicators directly, not wrapped in a Div with the WIZARD_STEPPER ID here.
    # The parent Div with id=WizardIDs.WIZARD_STEPPER will be in the layout file.
    return step_indicators
