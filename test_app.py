#!/usr/bin/env python3
"""Test script to verify the Flask app works with modular structure."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_app_creation():
    try:
        from app import create_app
        app = create_app()
        
        print("✅ Flask app created successfully!")
        print(f"✅ Blueprints registered: {list(app.blueprints.keys())}")
        
        # Test that we can access the rules
        with app.app_context():
            rules = list(app.url_map.iter_rules())
            animation_rules = [r for r in rules if 'animation' in r.endpoint]
            main_rules = [r for r in rules if 'main' in r.endpoint]
            api_rules = [r for r in rules if 'api' in r.endpoint]
            
            print(f"✅ Animation routes: {len(animation_rules)}")
            print(f"✅ Main routes: {len(main_rules)}")
            print(f"✅ API routes: {len(api_rules)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app_creation()
    print("✅ All tests passed!" if success else "❌ Tests failed!")
