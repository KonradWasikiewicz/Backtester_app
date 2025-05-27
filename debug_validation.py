#!/usr/bin/env python3
"""
Debug script to test Step 1 validation logic
"""

# Add project root to path
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the validation function
from src.ui.callbacks.wizard_validation_callbacks import validate_step_1

def test_validation():
    """Test various inputs to understand validation logic"""
    
    test_cases = [
        # (strategy, initial_capital, expected_result, description)
        ("buy_and_hold", 100000, True, "Valid strategy and capital"),
        ("buy_and_hold", 1000, True, "Valid strategy and minimum capital"),
        ("buy_and_hold", 999, False, "Valid strategy but capital too low"),
        ("buy_and_hold", None, False, "Valid strategy but no capital"),
        (None, 100000, False, "Valid capital but no strategy"),
        ("", 100000, False, "Empty strategy with valid capital"),
        ("buy_and_hold", "100000", True, "Valid strategy with string capital"),
        ("buy_and_hold", "100,000", True, "Valid strategy with formatted capital"),
        ("buy_and_hold", "", False, "Valid strategy with empty capital"),
        ("buy_and_hold", 0, False, "Valid strategy with zero capital"),
    ]
    
    print("Testing Step 1 validation logic:")
    print("=" * 50)
    
    for strategy, capital, expected, description in test_cases:
        result = validate_step_1(strategy, capital)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        print(f"{status} - {description}")
        print(f"   Input: strategy='{strategy}', capital={capital}")
        print(f"   Expected: {expected}, Got: {result}")
        print()
    
if __name__ == "__main__":
    test_validation()
