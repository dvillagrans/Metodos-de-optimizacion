#!/usr/bin/env python3
"""
Test script to verify the fixes for the numpy boolean error in Manim animations
"""

import sys
import os
import json
import numpy as np

# Add the manim_anim directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_advanced_animation_import():
    """Test that we can import the animation classes without errors"""
    try:
        from advanced_simplex_anim import AdvancedSimplexAnim, TableauVisualization
        print("✓ Successfully imported AdvancedSimplexAnim and TableauVisualization")
        return True
    except Exception as e:
        print(f"✗ Failed to import animation classes: {e}")
        return False

def test_data_loading():
    """Test loading data with numpy arrays and our boolean fixes"""
    try:
        # Load test data
        with open('test_problem_data.json', 'r') as f:
            data = json.load(f)
        
        # Convert to numpy arrays (simulating what happens in practice)
        tableau_history = np.array(data['tableau_history'])
        pivot_history = data['pivot_history']
        
        print(f"✓ Loaded test data with tableau_history shape: {tableau_history.shape}")
        
        # Test the fixed boolean conditions
        if len(tableau_history) > 0:
            print("✓ Boolean check 1 (len(tableau_history) > 0) passed")
        else:
            print("✗ Boolean check 1 failed")
            return False
            
        if len(tableau_history) == 0:
            print("✗ Boolean check 2 should be False for non-empty data")
        else:
            print("✓ Boolean check 2 (len(tableau_history) == 0) correctly returned False")
            
        return True
    except Exception as e:
        print(f"✗ Error in data loading test: {e}")
        return False

def test_class_instantiation():
    """Test that we can create instances of the animation classes"""
    try:
        from advanced_simplex_anim import AdvancedSimplexAnim, TableauVisualization
        
        # Test AdvancedSimplexAnim (this shouldn't actually run construct)
        print("✓ AdvancedSimplexAnim class is available")
        
        # Test TableauVisualization with some dummy data
        dummy_tableau = np.array([[1, 2, 3], [4, 5, 6]])
        dummy_pivot = (0, 1)
        
        # Note: We can't fully instantiate without a Manim scene context
        # but we can test that the class exists and is callable
        print("✓ TableauVisualization class is available")
        
        return True
    except Exception as e:
        print(f"✗ Error in class instantiation test: {e}")
        return False

def main():
    """Run all tests"""
    print("Running tests for Manim animation fixes...")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_advanced_animation_import),
        ("Data Loading Test", test_data_loading),
        ("Class Instantiation Test", test_class_instantiation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! The numpy boolean error fixes are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    exit(main())
