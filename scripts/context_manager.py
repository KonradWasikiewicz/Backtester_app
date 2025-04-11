#!/usr/bin/env python
"""
Context Manager for Backtester App

This script helps manage the project_context.md file which maintains persistent
context across development sessions. It can read, update, and validate the project context file.
"""

import os
import re
from datetime import datetime

CONTEXT_FILE_PATH = os.path.join('docs', 'project_context.md')

def read_context():
    """Read the current project context file"""
    try:
        with open(CONTEXT_FILE_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Context file not found at {CONTEXT_FILE_PATH}")
        return None

def update_user_preferences(new_preferences):
    """
    Update the User Preferences section of the context file
    
    Args:
        new_preferences (list): List of strings representing user preferences
    """
    try:
        with open(CONTEXT_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the User Preferences section
        user_pref_pattern = r"(## User Preferences\n)(.*?)(\n## )"
        user_pref_section = re.search(user_pref_pattern, content, re.DOTALL)
        
        if user_pref_section:
            # Format new preferences
            formatted_prefs = "\n".join([f"- {pref}" for pref in new_preferences])
            
            # Replace the content
            new_content = content.replace(
                user_pref_section.group(0),
                f"{user_pref_section.group(1)}{formatted_prefs}\n\n{user_pref_section.group(3)}"
            )
            
            # Update the last modified date
            date_pattern = r"\*Last updated: (.*?)\*"
            today = datetime.now().strftime("%B %d, %Y")
            new_content = re.sub(date_pattern, f"*Last updated: {today}*", new_content)
            
            # Write back to file
            with open(CONTEXT_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            print(f"Successfully updated user preferences in {CONTEXT_FILE_PATH}")
            return True
        else:
            print("Error: Couldn't find User Preferences section in context file")
            return False
            
    except Exception as e:
        print(f"Error updating context file: {str(e)}")
        return False

def add_technical_note(note):
    """
    Add a technical note to the context file
    
    Args:
        note (str): The technical note to add
    """
    try:
        with open(CONTEXT_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update the last modified date
        date_pattern = r"\*Last updated: (.*?)\*"
        today = datetime.now().strftime("%B %d, %Y")
        new_content = re.sub(date_pattern, f"*Last updated: {today}*", content)
        
        # Check if Technical Notes section exists
        if "## Technical Notes" not in new_content:
            # Add Technical Notes section before Documentation References
            doc_ref_pattern = r"(## Documentation References)"
            new_content = re.sub(
                doc_ref_pattern, 
                f"## Technical Notes\n- {note}\n\n\\1", 
                new_content
            )
        else:
            # Add note to existing Technical Notes section
            tech_notes_pattern = r"(## Technical Notes\n)(.*?)(\n## )"
            tech_notes_section = re.search(tech_notes_pattern, new_content, re.DOTALL)
            if tech_notes_section:
                existing_notes = tech_notes_section.group(2).strip()
                updated_notes = f"{existing_notes}\n- {note}"
                new_content = new_content.replace(
                    tech_notes_section.group(0),
                    f"{tech_notes_section.group(1)}{updated_notes}\n\n{tech_notes_section.group(3)}"
                )
        
        # Write back to file
        with open(CONTEXT_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"Successfully added technical note to {CONTEXT_FILE_PATH}")
        return True
    
    except Exception as e:
        print(f"Error updating context file: {str(e)}")
        return False

def validate_context():
    """Check if the context file exists and has the required sections"""
    try:
        content = read_context()
        if not content:
            return False
        
        required_sections = [
            "# Backtester App - Project Context",
            "## Purpose",
            "## Project Overview",
            "## Key Architectural Principles",
            "## User Preferences",
            "## Documentation References"
        ]
        
        for section in required_sections:
            if section not in content:
                print(f"Error: Required section '{section}' missing from context file")
                return False
        
        return True
    except Exception as e:
        print(f"Error validating context file: {str(e)}")
        return False

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python context_manager.py [read|validate|update_preferences|add_note] [args]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "read":
        context = read_context()
        if context:
            print(context)
    
    elif action == "validate":
        is_valid = validate_context()
        print(f"Context file is {'valid' if is_valid else 'invalid'}")
    
    elif action == "update_preferences":
        if len(sys.argv) < 3:
            print("Error: Please provide preferences to update")
            sys.exit(1)
        prefs = sys.argv[2:]
        update_user_preferences(prefs)
    
    elif action == "add_note":
        if len(sys.argv) < 3:
            print("Error: Please provide a note to add")
            sys.exit(1)
        note = " ".join(sys.argv[2:])
        add_technical_note(note)
    
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)