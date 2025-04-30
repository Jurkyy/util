#!/bin/bash

# Function to display usage information
usage() {
  echo "Usage: source $0 <path-to-env-file>"
  echo "Note: This script must be sourced, not executed directly"
  echo "Example: source $0 /path/to/.env"
}

# Check if the script is being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "Error: This script must be sourced, not executed directly"
  echo "Please use: source $0 <path-to-env-file>"
  exit 1
fi

# Check if a file path is provided
if [ -z "$1" ]; then
  usage
  return 1
fi

ENV_FILE="$1"

# Check if file exists
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: File not found: $ENV_FILE"
  return 1
fi

# Check if file is readable
if [ ! -r "$ENV_FILE" ]; then
  echo "Error: Cannot read file: $ENV_FILE"
  return 1
fi

# Counter for loaded variables
loaded_vars=0

# Read the .env file and export variables
while IFS= read -r line || [ -n "$line" ]; do
  # Skip empty lines and comments
  [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

  # Remove leading/trailing whitespace
  line="${line#"${line%%[![:space:]]*}"}"
  line="${line%"${line##*[![:space:]]}"}"

  # Only process valid variable assignments
  if [[ "$line" =~ ^[[:alnum:]_]+= ]]; then
    # Extract variable name (everything before first =)
    var_name="${line%%=*}"
    # Extract value (everything after first =)
    var_value="${line#*=}"

    # Remove surrounding quotes if present
    var_value="${var_value#[\"\']}"
    var_value="${var_value%[\"\']}"

    # Export the variable using printf to handle special characters
    printf -v "$var_name" '%s' "$var_value"
    export "$var_name"
    ((loaded_vars++))
  fi
done <"$ENV_FILE"

echo "Successfully loaded $loaded_vars environment variables from $ENV_FILE"

# Function to list loaded variables (optional)
list_vars() {
  echo "Loaded environment variables:"
  while IFS= read -r line || [ -n "$line" ]; do
    if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
      if [[ "$line" =~ ^[[:alnum:]_]+= ]]; then
        var_name="${line%%=*}"
        echo "  $var_name"
      fi
    fi
  done <"$ENV_FILE"
}
