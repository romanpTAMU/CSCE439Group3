#!/usr/bin/env python3
"""
Local test script to evaluate malware detection performance without Docker.
Uses the local inference service directly.
"""
import os
import sys
import time
from pathlib import Path
import concurrent.futures
from typing import Dict, List, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import local inference service
from defender.inference_service import score_exe

# Configuration
MAX_WORKERS = 4  # Parallel processing

def get_test_data_path() -> str:
    """Get test data path from user input with validation."""
    default_path = r"C:\Users\Roman\Downloads\challenge\challenge_ds"
    
    print("Enter the path to the challenge directory:")
    print(f"Default: {default_path}")
    print("Press Enter to use default, or type a custom path:")
    
    user_input = input().strip()
    
    if not user_input:
        test_path = default_path
    else:
        test_path = user_input
    
    # Validate path exists
    if not os.path.exists(test_path):
        print(f"❌ Path does not exist: {test_path}")
        print("Please check the path and try again.")
        sys.exit(1)
    
    # Validate it contains malware and goodware folders
    malware_path = Path(test_path) / "malware"
    goodware_path = Path(test_path) / "goodware"
    
    if not malware_path.exists():
        print(f"❌ Malware folder not found: {malware_path}")
        print("Expected structure: <challenge_dir>/malware/ and <challenge_dir>/goodware/")
        sys.exit(1)
    
    if not goodware_path.exists():
        print(f"❌ Goodware folder not found: {goodware_path}")
        print("Expected structure: <challenge_dir>/malware/ and <challenge_dir>/goodware/")
        sys.exit(1)
    
    return test_path

def test_file(file_path: Path) -> Tuple[bool, str]:
    """
    Test a single file against the local inference service.
    Returns (success, result_label)
    """
    try:
        result = score_exe(str(file_path))
        return True, str(result.get('label', 'unknown'))
    except Exception as e:
        return False, str(e)

def test_folder(folder_path: Path, expected_label: int) -> Dict:
    """
    Test all files in a folder and return statistics.
    """
    print(f"Testing {folder_path.name} ({'malware' if expected_label == 1 else 'goodware'})...")
    
    # Find all executable files - treat files without extensions as executables
    exe_files = []
    
    # First, get files with traditional executable extensions
    for ext in ['.exe', '.dll', '.sys', '.scr']:
        exe_files.extend(folder_path.glob(f"**/*{ext}"))
    
    # Then, get all files without extensions (treat as executables)
    for file_path in folder_path.glob("**/*"):
        if file_path.is_file() and not file_path.suffix:  # No extension
            exe_files.append(file_path)
    
    # Remove duplicates (in case a file has both patterns)
    exe_files = list(set(exe_files))
    
    if not exe_files:
        return {
            'folder': folder_path.name,
            'expected': expected_label,
            'total_files': 0,
            'correct': 0,
            'success_rate': 0.0,
            'errors': []
        }
    
    print(f"  Found {len(exe_files)} executable files")
    
    # Test files in parallel
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_file = {
            executor.submit(test_file, file_path): file_path 
            for file_path in exe_files
        }
        
        for future in concurrent.futures.as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                success, result = future.result()
                results.append((success, result, file_path))
            except Exception as e:
                results.append((False, str(e), file_path))
    
    # Calculate statistics
    correct = 0
    errors = []
    
    for success, result, file_path in results:
        if success:
            try:
                predicted_label = int(result)
                if predicted_label == expected_label:
                    correct += 1
            except ValueError:
                errors.append(f"{file_path.name}: Invalid label '{result}'")
        else:
            errors.append(f"{file_path.name}: {result}")
    
    success_rate = (correct / len(exe_files)) * 100 if exe_files else 0.0
    
    return {
        'folder': folder_path.name,
        'expected': expected_label,
        'total_files': len(exe_files),
        'correct': correct,
        'success_rate': success_rate,
        'errors': errors[:5]  # Show first 5 errors
    }

def check_local_service() -> bool:
    """Check if local inference service can be imported and used."""
    try:
        # Try to import and test with a dummy path
        from defender.inference_service import score_exe
        return True
    except Exception as e:
        print(f"❌ Local inference service error: {e}")
        return False

def main():
    print("XGBoost Malware Detection - Local Test Suite")
    print("=" * 50)
    
    # Check local service
    print("Checking local inference service...")
    if not check_local_service():
        print("❌ Local inference service not available")
        print("Make sure you're running from the project root and all dependencies are installed")
        sys.exit(1)
    print("✅ Local inference service is available")
    
    # Get test data path from user
    test_data_path = get_test_data_path()
    test_path = Path(test_data_path)
    
    malware_path = test_path / "malware"
    goodware_path = test_path / "goodware"
    
    print(f"📁 Test data path: {test_path}")
    print(f"📁 Malware folders: {len(list(malware_path.iterdir()))}")
    print(f"📁 Goodware folders: {len(list(goodware_path.iterdir()))}")
    print()
    
    # Test malware folders
    print("🔴 TESTING MALWARE FOLDERS")
    print("-" * 30)
    malware_results = []
    for folder in sorted(malware_path.iterdir()):
        if folder.is_dir():
            result = test_folder(folder, expected_label=1)
            malware_results.append(result)
            print(f"malware: {result['folder']} success - {result['success_rate']:.1f}% ({result['correct']}/{result['total_files']})")
            if result['errors']:
                print(f"  Errors: {', '.join(result['errors'])}")
    
    print()
    
    # Test goodware folders
    print("🟢 TESTING GOODWARE FOLDERS")
    print("-" * 30)
    goodware_results = []
    for folder in sorted(goodware_path.iterdir()):
        if folder.is_dir():
            result = test_folder(folder, expected_label=0)
            goodware_results.append(result)
            print(f"goodware: {result['folder']} success - {result['success_rate']:.1f}% ({result['correct']}/{result['total_files']})")
            if result['errors']:
                print(f"  Errors: {', '.join(result['errors'])}")
    
    print()
    
    # Summary statistics
    print("📊 SUMMARY STATISTICS")
    print("=" * 50)
    
    all_malware_files = sum(r['total_files'] for r in malware_results)
    all_malware_correct = sum(r['correct'] for r in malware_results)
    malware_avg = (all_malware_correct / all_malware_files * 100) if all_malware_files > 0 else 0
    
    all_goodware_files = sum(r['total_files'] for r in goodware_results)
    all_goodware_correct = sum(r['correct'] for r in goodware_results)
    goodware_avg = (all_goodware_correct / all_goodware_files * 100) if all_goodware_files > 0 else 0
    
    total_files = all_malware_files + all_goodware_files
    total_correct = all_malware_correct + all_goodware_correct
    overall_accuracy = (total_correct / total_files * 100) if total_files > 0 else 0
    
    print(f"Malware Detection Rate: {malware_avg:.1f}% ({all_malware_correct}/{all_malware_files})")
    print(f"Goodware Detection Rate: {goodware_avg:.1f}% ({all_goodware_correct}/{all_goodware_files})")
    print(f"Overall Accuracy: {overall_accuracy:.1f}% ({total_correct}/{total_files})")
    
    # False positive/negative rates
    false_negatives = all_malware_files - all_malware_correct
    false_positives = all_goodware_files - all_goodware_correct
    
    fnr = (false_negatives / all_malware_files * 100) if all_malware_files > 0 else 0
    fpr = (false_positives / all_goodware_files * 100) if all_goodware_files > 0 else 0
    
    print(f"False Negative Rate: {fnr:.1f}%")
    print(f"False Positive Rate: {fpr:.1f}%")

if __name__ == "__main__":
    main()
