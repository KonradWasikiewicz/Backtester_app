#!/usr/bin/env python
"""
Context Loader for Backtester App

This script loads the project context and prints it in a format that can be used
at the beginning of conversations to maintain consistent understanding of the project.
"""

import os
import sys
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.context_manager import read_context, validate_context

def format_context_for_conversation():
    """Format the project context for use in conversations"""
    if not validate_context():
        print("Error: Project context is invalid or missing")
        return None
    
    context = read_context()
    if not context:
        return None
    
    # Extract key sections for conversation context
    # We don't need the entire file, just the important parts
    sections = [
        "Project Overview",
        "Key Architectural Principles",
        "Design Guidelines",
        "Technical Stack",
        "Language Requirements",
        "User Preferences",
        "Technical Notes"
    ]
    
    conversation_context = "# Backtester App - Essential Context\n\n"
    
    for section in sections:
        pattern = f"## {section}(.*?)(?=\n## |\Z)"
        match = re.search(pattern, context, re.DOTALL)
        if match:
            section_content = match.group(1).strip()
            conversation_context += f"## {section}\n{section_content}\n\n"
    
    # Add reference to full documentation
    conversation_context += "For complete details, refer to the documentation in the docs folder.\n"
    
    return conversation_context

if __name__ == "__main__":
    formatted_context = format_context_for_conversation()
    if formatted_context:
        print(formatted_context)
        
        # If an output file is specified, write to it
        if len(sys.argv) > 1:
            output_file = sys.argv[1]
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(formatted_context)
                print(f"Context written to {output_file}")
            except Exception as e:
                print(f"Error writing to {output_file}: {str(e)}")
    else:
        print("Failed to generate conversation context")