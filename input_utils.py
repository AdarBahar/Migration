#!/usr/bin/env python3
"""
Input Utilities
Provides enhanced input functions with readline support for better text editing.
Supports backspace, arrow keys, and command history.
"""

import sys

def setup_readline():
    """Setup readline for better input editing if available."""
    try:
        import readline
        import rlcompleter
        
        # Enable tab completion
        if 'libedit' in readline.__doc__:
            # macOS uses libedit
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            # Linux uses GNU readline
            readline.parse_and_bind("tab: complete")
        
        # Set history file
        import os
        histfile = os.path.join(os.path.expanduser("~"), ".migration_history")
        try:
            readline.read_history_file(histfile)
            # Default history len is -1 (infinite), which may grow unruly
            readline.set_history_length(1000)
        except FileNotFoundError:
            pass
        
        # Save history on exit
        import atexit
        atexit.register(readline.write_history_file, histfile)
        
        return True
    except ImportError:
        # readline not available (Windows without pyreadline)
        return False

# Initialize readline on module import
_READLINE_AVAILABLE = setup_readline()

def get_input(prompt="", default=None):
    """
    Get input with readline support for backspace and arrow keys.
    
    Args:
        prompt: The prompt to display
        default: Default value to show in brackets
    
    Returns:
        User input string
    """
    if default is not None:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: " if prompt and not prompt.endswith(": ") else prompt
    
    try:
        user_input = input(full_prompt).strip()
        
        # Return default if user just pressed Enter
        if not user_input and default is not None:
            return str(default)
        
        return user_input
    except EOFError:
        # Handle Ctrl+D
        print()
        return ""
    except KeyboardInterrupt:
        # Handle Ctrl+C
        print()
        raise

def get_yes_no(prompt, default=True):
    """
    Get yes/no input from user.
    
    Args:
        prompt: The prompt to display
        default: Default value (True for yes, False for no)
    
    Returns:
        Boolean value
    """
    default_str = "Y/n" if default else "y/N"
    full_prompt = f"{prompt} ({default_str})"
    
    while True:
        response = get_input(full_prompt).lower()
        
        if not response:
            return default
        
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("❌ Please enter 'y' for yes or 'n' for no")

def get_choice(prompt, choices, default=None):
    """
    Get a choice from a list of options.
    
    Args:
        prompt: The prompt to display
        choices: List of valid choices
        default: Default choice if user presses Enter
    
    Returns:
        Selected choice
    """
    while True:
        response = get_input(prompt, default)
        
        if response in choices:
            return response
        else:
            print(f"❌ Invalid choice. Please select from: {', '.join(choices)}")

def get_number(prompt, min_val=None, max_val=None, default=None):
    """
    Get a number from user with optional range validation.
    
    Args:
        prompt: The prompt to display
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        default: Default value
    
    Returns:
        Integer value
    """
    while True:
        try:
            response = get_input(prompt, default)
            
            if not response:
                if default is not None:
                    return int(default)
                else:
                    print("❌ Please enter a number")
                    continue
            
            value = int(response)
            
            if min_val is not None and value < min_val:
                print(f"❌ Value must be at least {min_val}")
                continue
            
            if max_val is not None and value > max_val:
                print(f"❌ Value must be at most {max_val}")
                continue
            
            return value
        
        except ValueError:
            print("❌ Please enter a valid number")

def get_multiline_input(prompt="Enter text (Ctrl+D or empty line to finish):"):
    """
    Get multiple lines of input from user.
    
    Args:
        prompt: The prompt to display
    
    Returns:
        List of input lines
    """
    print(prompt)
    lines = []
    
    try:
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
    except EOFError:
        pass
    
    return lines

def confirm_action(action, default=False):
    """
    Ask user to confirm an action.
    
    Args:
        action: Description of the action to confirm
        default: Default response
    
    Returns:
        Boolean confirmation
    """
    return get_yes_no(f"⚠️  {action}. Continue?", default)

def pause(message="Press Enter to continue..."):
    """
    Pause execution until user presses Enter.
    
    Args:
        message: Message to display
    """
    try:
        input(message)
    except (EOFError, KeyboardInterrupt):
        print()

def clear_screen():
    """Clear the terminal screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title, width=80):
    """
    Print a formatted header.
    
    Args:
        title: Header title
        width: Width of the header
    """
    print("\n" + "=" * width)
    print(title.center(width))
    print("=" * width)

def print_section(title, width=80):
    """
    Print a formatted section header.
    
    Args:
        title: Section title
        width: Width of the section
    """
    print("\n" + title)
    print("-" * width)

# Export readline availability status
def is_readline_available():
    """Check if readline is available for enhanced input editing."""
    return _READLINE_AVAILABLE

