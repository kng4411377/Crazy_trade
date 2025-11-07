#!/usr/bin/env python3
"""
Cross-platform test runner for Crazy Trade Bot.
Python-based alternative to run_tests.sh for Windows compatibility.
"""

import sys
import argparse
import subprocess
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and return the exit code."""
    if description:
        print(f"\n{'='*60}")
        print(f"  {description}")
        print('='*60)
    
    result = subprocess.run(cmd, shell=False)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description='Run tests for the Crazy Trade Bot project.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py              # Run all tests
  python run_tests.py --unit       # Run unit tests only
  python run_tests.py --coverage   # Run with coverage report
  python run_tests.py --file test_api_server.py
  python run_tests.py --fast       # Run tests quickly
        """
    )
    
    parser.add_argument(
        '--unit',
        action='store_true',
        help='Run only unit tests'
    )
    parser.add_argument(
        '--integration',
        action='store_true',
        help='Run only integration tests'
    )
    parser.add_argument(
        '--api',
        action='store_true',
        help='Run only API tests'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run tests with coverage report'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Run specific test file (e.g., test_database.py)'
    )
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Run tests without verbosity (fast mode)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output (default is already verbose)'
    )
    
    args = parser.parse_args()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    
    # Check if pytest is available
    try:
        subprocess.run(['pytest', '--version'], 
                      capture_output=True, 
                      check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: pytest is not installed!")
        print("Install it with: pip install -r requirements.txt")
        return 1
    
    # Build pytest command
    cmd = ['pytest']
    
    # Determine which tests to run
    if args.file:
        test_path = script_dir / 'tests' / args.file
        if not test_path.exists():
            test_path = Path(args.file)
            if not test_path.exists():
                print(f"❌ Error: Test file not found: {args.file}")
                return 1
        cmd.append(str(test_path))
        description = f"Running Test File: {args.file}"
    elif args.unit:
        cmd.extend(['tests/', '-m', 'unit'])
        description = "Running Unit Tests"
    elif args.integration:
        cmd.extend(['tests/', '-m', 'integration'])
        description = "Running Integration Tests"
    elif args.api:
        cmd.append('tests/test_api_server.py')
        description = "Running API Tests"
    else:
        cmd.append('tests/')
        description = "Running All Tests"
    
    # Add options
    if args.coverage:
        cmd.extend(['--cov=src', '--cov-report=html', '--cov-report=term'])
        description += " with Coverage"
    
    if args.fast:
        cmd.extend(['--tb=short', '-q'])
    else:
        cmd.append('-v')
    
    # Run the tests
    exit_code = run_command(cmd, description)
    
    # Print results
    print()
    if exit_code == 0:
        print("✅ All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print("❌ Some tests failed!")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())

