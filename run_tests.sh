#!/bin/bash

# Test runner script for Crazy Trade Bot
# Runs pytest with various configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv/bin" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Function to print colored output
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to display usage
usage() {
    cat << EOF
Usage: ./run_tests.sh [OPTIONS]

Run tests for the Crazy Trade Bot project.

OPTIONS:
    all             Run all tests (default)
    unit            Run only unit tests
    integration     Run only integration tests
    api             Run only API tests
    coverage        Run all tests with coverage report
    file <name>     Run specific test file (e.g., test_database.py)
    fast            Run tests without verbosity
    -h, --help      Show this help message

EXAMPLES:
    ./run_tests.sh                    # Run all tests
    ./run_tests.sh unit               # Run unit tests only
    ./run_tests.sh coverage           # Run with coverage report
    ./run_tests.sh file test_api_server.py
    ./run_tests.sh fast               # Run tests quickly

EOF
}

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_error "pytest is not installed!"
    echo "Install it with: pip install -r requirements.txt"
    exit 1
fi

# Parse command line arguments
case "${1:-all}" in
    all)
        print_header "Running All Tests"
        pytest tests/ -v
        ;;
    
    unit)
        print_header "Running Unit Tests"
        pytest tests/ -v -m unit
        ;;
    
    integration)
        print_header "Running Integration Tests"
        pytest tests/ -v -m integration
        ;;
    
    api)
        print_header "Running API Tests"
        pytest tests/test_api_server.py -v
        ;;
    
    coverage)
        print_header "Running Tests with Coverage"
        if ! command -v coverage &> /dev/null; then
            print_warning "coverage not installed, using pytest-cov instead"
            pytest tests/ -v --cov=src --cov-report=html --cov-report=term
            print_success "Coverage report generated in htmlcov/index.html"
        else
            coverage run -m pytest tests/
            coverage report
            coverage html
            print_success "Coverage report generated in htmlcov/index.html"
        fi
        ;;
    
    fast)
        print_header "Running Tests (Fast Mode)"
        pytest tests/ --tb=short -q
        ;;
    
    file)
        if [ -z "$2" ]; then
            print_error "Please specify a test file"
            echo "Usage: ./run_tests.sh file <test_file.py>"
            exit 1
        fi
        print_header "Running Test File: $2"
        if [ -f "tests/$2" ]; then
            pytest "tests/$2" -v
        elif [ -f "$2" ]; then
            pytest "$2" -v
        else
            print_error "Test file not found: $2"
            exit 1
        fi
        ;;
    
    -h|--help)
        usage
        exit 0
        ;;
    
    *)
        print_error "Unknown option: $1"
        echo ""
        usage
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    print_success "All tests passed!"
    exit 0
else
    print_error "Some tests failed!"
    exit 1
fi

