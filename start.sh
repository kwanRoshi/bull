#!/bin/bash

# Function to run tests
run_tests() {
    echo "Running tests..."
    pytest
    
    # Check test coverage
    coverage_threshold=90
    coverage_result=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
    
    if (( $(echo "$coverage_result < $coverage_threshold" | bc -l) )); then
        echo "Test coverage ($coverage_result%) is below threshold ($coverage_threshold%)"
        exit 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --test)
            # Install dependencies and run tests
            pip install -r requirements.txt
            run_tests
            exit 0
            ;;
        *)
            break
            ;;
    esac
    shift
done

# Install dependencies if not already installed
pip install -r requirements.txt

# Run the bot
python -m crypto_twitter_bot.crypto_twitter_bot 