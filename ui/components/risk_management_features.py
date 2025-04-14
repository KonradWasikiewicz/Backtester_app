import gradio as gr
from typing import Dict, List, Any, Callable

def risk_management_features(state_manager: Any = None) -> Dict:
    """
    Creates the risk management features UI component.
    
    Returns:
        Dictionary containing the risk management features UI components.
    """
    with gr.Column() as risk_management_container:
        gr.Markdown("### Risk Management Features")
        
        # Enable Stop Loss checkbox
        enable_stop_loss = gr.Checkbox(label="Enable Stop Loss", value=False)
        
        # Stop Loss fields (initially hidden, now directly below the checkbox)
        with gr.Column(visible=False) as stop_loss_container:
            stop_loss_type = gr.Dropdown(
                label="Stop Loss Type",
                choices=["Fixed", "Trailing", "ATR"],
                value="Fixed"
            )
            stop_loss_value = gr.Number(label="Stop Loss Value", value=5, precision=2)
        
        # Enable Take Profit checkbox
        enable_take_profit = gr.Checkbox(label="Enable Take Profit", value=False)
        
        # Take Profit fields (initially hidden, now directly below the checkbox)
        with gr.Column(visible=False) as take_profit_container:
            take_profit_type = gr.Dropdown(
                label="Take Profit Type",
                choices=["Fixed", "Trailing"],
                value="Fixed"
            )
            take_profit_value = gr.Number(label="Take Profit Value", value=10, precision=2)
        
        # Enable Position Sizing checkbox
        enable_position_sizing = gr.Checkbox(label="Enable Position Sizing", value=False)
        
        # Position Sizing fields (initially hidden, now directly below the checkbox)
        with gr.Column(visible=False) as position_sizing_container:
            position_sizing_type = gr.Dropdown(
                label="Position Sizing Type",
                choices=["Fixed", "Percentage of Capital", "Risk-based"],
                value="Fixed"
            )
            position_sizing_value = gr.Number(label="Position Sizing Value", value=1000, precision=2)
        
        # Enable Pyramiding checkbox
        enable_pyramiding = gr.Checkbox(label="Enable Pyramiding", value=False)
        
        # Pyramiding fields (initially hidden, now directly below the checkbox)
        with gr.Column(visible=False) as pyramiding_container:
            max_positions = gr.Number(label="Maximum Positions", value=3, precision=0)
            position_scale = gr.Number(label="Position Scale", value=0.5, precision=2)
        
        # Add Continue to iterate checkbox with improved label and tooltip
        continue_iterate = gr.Checkbox(
            label="Continue iteration after stop conditions", 
            value=False,
            info="When enabled, the strategy will continue testing iterations even after encountering stop loss or take profit conditions. This allows for analysis of what would have happened if positions were maintained."
        )
        
        # Event handlers for showing/hiding fields
        enable_stop_loss.change(
            fn=lambda x: gr.update(visible=x),
            inputs=[enable_stop_loss],
            outputs=[stop_loss_container]
        )
        
        enable_take_profit.change(
            fn=lambda x: gr.update(visible=x),
            inputs=[enable_take_profit],
            outputs=[take_profit_container]
        )
        
        enable_position_sizing.change(
            fn=lambda x: gr.update(visible=x),
            inputs=[enable_position_sizing],
            outputs=[position_sizing_container]
        )
        
        enable_pyramiding.change(
            fn=lambda x: gr.update(visible=x),
            inputs=[enable_pyramiding],
            outputs=[pyramiding_container]
        )
        
    return {
        "risk_management_container": risk_management_container,
        "enable_stop_loss": enable_stop_loss,
        "stop_loss_type": stop_loss_type,
        "stop_loss_value": stop_loss_value,
        "enable_take_profit": enable_take_profit,
        "take_profit_type": take_profit_type,
        "take_profit_value": take_profit_value,
        "enable_position_sizing": enable_position_sizing,
        "position_sizing_type": position_sizing_type,
        "position_sizing_value": position_sizing_value,
        "enable_pyramiding": enable_pyramiding,
        "max_positions": max_positions,
        "position_scale": position_scale,
        "continue_iterate": continue_iterate
    }
