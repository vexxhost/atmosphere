#!/bin/bash -x

# Check if an argument was provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_save_logs>"
    exit 1
fi

# Define the base directory where you want to save the logs
BASE_DIR="$1"

# Create the base directory if it doesn't exist
mkdir -p "$BASE_DIR"

# Function to fetch logs for a pod and container
fetch_logs() {
    local ns="$1"
    local pod="$2"
    local container="$3"
    local pod_dir="$BASE_DIR/$ns/$pod"
    local log_file="$pod_dir/$container.log"
    local prev_log_file="$pod_dir/${container}-previous.log"

    # Ensure the pod directory exists
    mkdir -p "$pod_dir"

    # Fetch current logs
    kubectl logs "$pod" -n "$ns" -c "$container" > "$log_file" 2>/dev/null

    # Fetch previous logs if they exist
    if kubectl logs "$pod" -n "$ns" -c "$container" --previous &>/dev/null; then
        kubectl logs "$pod" -n "$ns" -c "$container" --previous > "$prev_log_file" 2>/dev/null
    fi
}

export -f fetch_logs
export BASE_DIR

# Get all namespaces
namespaces=$(kubectl get ns -o jsonpath='{.items[*].metadata.name}')

# Loop through each namespace
for ns in $namespaces; do
    (
        # Create a directory for the namespace
        mkdir -p "$BASE_DIR/$ns"

        # Get all pods in the namespace
        pods=$(kubectl get pods -n "$ns" -o jsonpath='{.items[*].metadata.name}')

        # Loop through each pod
        for pod in $pods; do
            (
                # Create a directory for the pod
                mkdir -p "$BASE_DIR/$ns/$pod"

                # Get all containers in the pod
                containers=$(kubectl get pod "$pod" -n "$ns" -o jsonpath='{.spec.containers[*].name}')

                # Loop through each container
                for container in $containers; do
                    # Fetch logs in parallel
                    fetch_logs "$ns" "$pod" "$container" &
                done

                # Wait for all background log fetches to complete before moving to the next pod
                wait
            ) &
        done
        # Wait for all background pods processing to complete before moving to the next namespace
        wait
    ) &
done

# Wait for all background namespaces processing to complete
wait

echo "Logs have been saved to $BASE_DIR"
