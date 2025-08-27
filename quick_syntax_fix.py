#!/usr/bin/env python3
"""
Quick syntax fix for opportunity_zone_analyzer.py
This will create a working version by fixing the most obvious syntax issues.
"""

import re

def fix_syntax():
    """Fix the syntax errors in opportunity_zone_analyzer.py"""
    
    with open('opportunity_zone_analyzer.py', 'r') as f:
        content = f.read()
    
    # The main issue seems to be the complex f-string with embedded multi-line logger statements
    # Let's find and fix the generate_deep_research_prompt method
    
    # Find the method and replace it with a simpler version
    pattern = r'def generate_deep_research_prompt\(self, zone: Dict\[str, Any\], initial_research: str\) -> str:.*?return prompt'
    
    replacement = '''def generate_deep_research_prompt(self, zone: Dict[str, Any], initial_research: str) -> str:
        """Generate a deep research prompt using the initial market research results."""
        zone_name = zone.get('name', 'Unknown Zone')
        market_score = zone.get('market_opportunity_score', 0)
        initial_insights = initial_research[:1000] if initial_research else "No initial research available"
        
        prompt = (
            "Deep Strategic Market Analysis\\n\\n"
            f"Zone: {zone_name}\\n"
            f"Market Score: {market_score}\\n\\n"
            f"Initial Research: {initial_insights}\\n\\n"
            "Please provide:\\n"
            "1. Market opportunities and threats\\n"
            "2. Strategic product recommendations\\n"
            "3. Revenue models and business opportunities\\n"
            "4. Risk assessment and mitigation strategies\\n"
            "5. Key stakeholders and market dynamics"
        )
        return prompt'''
    
    # Use DOTALL flag to match across newlines
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        with open('opportunity_zone_analyzer.py', 'w') as f:
            f.write(new_content)
        print("✅ Fixed generate_deep_research_prompt method")
    else:
        print("⚠️  Could not find/fix the method - pattern didn't match")
    
    # Test if it compiles now
    try:
        compile(new_content, 'opportunity_zone_analyzer.py', 'exec')
        print("✅ File compiles without syntax errors")
        return True
    except SyntaxError as e:
        print(f"❌ Still has syntax error at line {e.lineno}: {e.msg}")
        return False

if __name__ == "__main__":
    print("🔧 Attempting quick syntax fix...")
    if fix_syntax():
        print("🎉 Syntax fixed! Pipeline should work now.")
    else:
        print("⚠️  Manual intervention still needed.")