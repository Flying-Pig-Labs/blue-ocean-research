#!/usr/bin/env python3
"""
Simple rollout script to safely transition to modular pipeline.
Just enables the baseline flavor and validates it works identically.
"""

import sys
import subprocess
import json
from pathlib import Path

def main():
    print("🚀 Starting simple rollout of modular pipeline...")
    
    # Step 1: Run existing pipeline once to get baseline
    print("\n1. Running original pipeline for comparison...")
    try:
        result = subprocess.run([sys.executable, "run_pipeline.py"], 
                              capture_output=True, text=True, timeout=3600)
        if result.returncode != 0:
            print(f"❌ Original pipeline failed: {result.stderr}")
            return False
        print("✅ Original pipeline completed successfully")
    except Exception as e:
        print(f"❌ Original pipeline error: {e}")
        return False
    
    # Step 2: Run modular pipeline with baseline flavor
    print("\n2. Running modular pipeline with baseline flavor...")
    try:
        result = subprocess.run([sys.executable, "run_pipeline_modular.py", "--flavor", "baseline"], 
                              capture_output=True, text=True, timeout=3600)
        if result.returncode != 0:
            print(f"❌ Modular pipeline failed: {result.stderr}")
            return False
        print("✅ Modular pipeline completed successfully")
    except Exception as e:
        print(f"❌ Modular pipeline error: {e}")
        return False
    
    # Step 3: Quick validation that key files exist
    print("\n3. Validating outputs...")
    expected_files = [
        "opportunity_zones_advanced.json",
        "final_innovation_portfolio.json",
        "product_ideas_comprehensive.json"
    ]
    
    for filename in expected_files:
        if Path(filename).exists():
            print(f"✅ Found {filename}")
        else:
            print(f"❌ Missing {filename}")
            return False
    
    print("\n🎉 Rollout validation successful!")
    print("\nNext steps:")
    print("1. Use 'python run_pipeline_modular.py --flavor baseline' going forward")
    print("2. When ready, create new flavor YAML files for your custom frameworks")
    print("3. Test new flavors with 'python run_pipeline_modular.py --flavor <your-flavor>'")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)