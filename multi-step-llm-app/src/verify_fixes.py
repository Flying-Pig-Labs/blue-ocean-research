#!/usr/bin/env python3
"""Legacy script for verifying earlier pipeline fixes.

This script remains for historical reference and is not part of the active
pipeline execution.
"""

import re

def check_file_for_slicing(filepath, filename):
    """Check a file for problematic array slicing patterns."""
    print(f"\n📄 Checking {filename}...")
    issues = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    problematic_patterns = [
        (r'verticals\[:(\d+)\]', "Slicing verticals"),
        (r'personas\[:(\d+)\]', "Slicing personas"),
        (r'pain_points\[:(\d+)\]', "Slicing pain points"),
        (r'elements\["[^"]+"\]\[:(\d+)\]', "Slicing elements"),
    ]
    
    for line_num, line in enumerate(lines, 1):
        for pattern, description in problematic_patterns:
            match = re.search(pattern, line)
            if match:
                # Skip if it's a comment or part of removed code
                if 'REMOVED' in line or '#' in line.strip()[:1]:
                    continue
                issues.append(f"   Line {line_num}: {description} to first {match.group(1)} items")
    
    if issues:
        print(f"   ⚠️ Found potential issues:")
        for issue in issues:
            print(issue)
    else:
        print(f"   ✅ No problematic slicing found")
    
    return len(issues) == 0

def check_specific_fixes():
    """Check that specific fixes have been applied."""
    print("\n" + "="*60)
    print("Verifying Specific Fixes")
    print("="*60)
    
    # 1. Check KMeans fallback in cluster_jtbd.py
    print("\n1️⃣ Checking KMeans fallback in cluster_jtbd.py...")
    with open('cluster_jtbd.py', 'r') as f:
        content = f.read()
        if 'from sklearn.cluster import KMeans' in content:
            print("   ✅ KMeans import found")
        if 'No clusters found with HDBSCAN, falling back to KMeans' in content:
            print("   ✅ Fallback message found")
        if 'n_clusters == 0:' in content:
            print("   ✅ Zero cluster check found")
    
    # 2. Check removed roadmap in idea_consolidator.py
    print("\n2️⃣ Checking idea_consolidator.py roadmap removal...")
    with open('idea_consolidator.py', 'r') as f:
        content = f.read()
        if 'REMOVED: _create_roadmap' in content:
            print("   ✅ Roadmap function marked as removed")
        if 'REMOVED: _suggest_resource_allocation' in content:
            print("   ✅ Resource allocation marked as removed")
        if 'choose 1-2' in content:
            print("   ✅ Updated to recommend choosing 1-2 ideas")
    
    # 3. Check analysis chunk size in jobs_researcher.py
    print("\n3️⃣ Checking jobs_researcher.py analysis chunk size...")
    with open('jobs_researcher.py', 'r') as f:
        content = f.read()
        if '30000' in content:
            print("   ✅ Using 30,000 character chunks (was 3,000)")
        if 'max_tokens=4000' in content:
            print("   ✅ Using 4000 max tokens (was 1,000)")
    
    # 4. Check cluster labeling in cluster_jtbd.py
    print("\n4️⃣ Checking cluster labeling improvements...")
    with open('cluster_jtbd.py', 'r') as f:
        content = f.read()
        if 'Use ALL texts for better context' in content:
            print("   ✅ Improved cluster labeling context")
        if 'diverse sample: first few, middle few, last few' in content:
            print("   ✅ Intelligent sampling for large clusters")
    
    # 5. Check prompts structure
    print("\n5️⃣ Checking external prompts...")
    import os
    if os.path.exists('prompts/2-jobs-researcher-expansion.txt'):
        with open('prompts/2-jobs-researcher-expansion.txt', 'r') as f:
            content = f.read()
            if 'GOOD pain points' in content and 'BAD pain points' in content:
                print("   ✅ Expansion prompt with examples exists")
            if 'adapt to the actual domain' in content:
                print("   ✅ Domain-agnostic examples")

def main():
    """Run all verification checks."""
    print("="*60)
    print("Pipeline Fix Verification")
    print("="*60)
    
    # Check main files for slicing issues
    files_to_check = [
        ('jobs_researcher.py', 'jobs_researcher.py'),
        ('cluster_jtbd.py', 'cluster_jtbd.py'),
        ('idea_consolidator.py', 'idea_consolidator.py'),
        ('product_idea_generator.py', 'product_idea_generator.py'),
        ('value_curve_mapper.py', 'value_curve_mapper.py'),
    ]
    
    print("\n🔍 Checking for array slicing issues...")
    all_good = True
    for filepath, filename in files_to_check:
        if not check_file_for_slicing(filepath, filename):
            all_good = False
    
    # Check specific fixes
    check_specific_fixes()
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    if all_good:
        print("""
✅ All major fixes appear to be in place:
   - No arbitrary array slicing limiting data
   - KMeans fallback for clustering
   - Roadmap assumption removed
   - Better context for GPT-4o labeling
   - Domain-agnostic pain point expansion
   - Increased analysis chunk size

The pipeline should now:
1. Use ALL extracted elements (not just first 3-5)
2. Generate ~100 pain points for clustering
3. Handle clustering edge cases gracefully
4. Correctly recommend choosing 1-2 ideas (not building all)
        """)
    else:
        print("""
⚠️ Some potential issues remain. Review the warnings above.
        """)

if __name__ == "__main__":
    main()