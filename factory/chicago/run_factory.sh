#!/bin/bash

# Define log file
LOG_FILE="pipeline_$(date +%Y%m%d_%H%M%S).log"

# Helper function to run and log commands
run_step() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running: $*" | tee -a "$LOG_FILE"
    "$@" >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Command failed: $*" | tee -a "$LOG_FILE"
        exit 1
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS" | tee -a "$LOG_FILE"
    fi
    echo "" | tee -a "$LOG_FILE"
}

echo "Starting data pipeline..." | tee "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Run all steps
run_step python -m factory.chicago.owner --backend neo4j --file Business_Owners_20240103.csv
run_step python -m factory.chicago.owner_cluster --backend neo4j
run_step python -m factory.chicago.contract --backend neo4j --file Contracts_20240103.csv
run_step python -m factory.chicago.license --backend neo4j --file Business_Licenses_20240103.csv
run_step python -m factory.chicago.org_cluster --backend neo4j

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline completed successfully." | tee -a "$LOG_FILE"
