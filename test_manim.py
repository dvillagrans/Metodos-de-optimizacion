#!/usr/bin/env python3
"""
Test script for Manim animation generation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from manim_renderer import generate_manim_animation

def test_basic_animation():
    """Test basic animation generation with sample data"""
    
    # Sample optimization problem data
    c = [3, 2]  # Objective function coefficients
    A = [[1, 2], [2, 1], [1, 0], [0, 1]]  # Constraint matrix
    b = [4, 6, 3, 2]  # Right-hand side values
    solution = [2.0, 1.0]  # Optimal solution
    z_opt = 8.0  # Optimal value
    minimize = False  # Maximization problem
    method = "simplex"
    
    print("Testing Manim animation generation...")
    print(f"Problem: Maximize Z = {c[0]}x₁ + {c[1]}x₂")
    print("Subject to:")
    for i, (row, rhs) in enumerate(zip(A, b)):
        constraint = " + ".join([f"{coef}x₍{j+1}₎" for j, coef in enumerate(row)])
        print(f"  {constraint} ≤ {rhs}")
    print(f"Solution: x₁ = {solution[0]}, x₂ = {solution[1]}")
    print(f"Optimal value: Z = {z_opt}")
    print()
    
    # Generate animation
    result = generate_manim_animation(
        c=c,
        A=A,
        b=b,
        solution=solution,
        z_opt=z_opt,
        minimize=minimize,
        method=method
    )
    
    if result:
        print(f"✅ Animation generated successfully!")
        print(f"📁 Output file: {result}")
        
        # Check if file exists
        if os.path.exists(result):
            file_size = os.path.getsize(result) / 1024  # Size in KB
            print(f"📊 File size: {file_size:.2f} KB")
            
            # Determine file type
            if result.endswith('.mp4'):
                print("🎥 Generated video file (MP4)")
            elif result.endswith('.png'):
                print("🖼️ Generated image file (PNG)")
            else:
                print(f"📄 Generated file: {os.path.splitext(result)[1]}")
        else:
            print("⚠️ Output file not found at specified path")
    else:
        print("❌ Animation generation failed")
    
    return result

if __name__ == "__main__":
    result = test_basic_animation()
    
    if result:
        print("\n" + "="*50)
        print("🎉 Test completed successfully!")
        print("You can find the generated animation in the output folder.")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("💥 Test failed!")
        print("Check the logs above for error details.")
        print("="*50)
