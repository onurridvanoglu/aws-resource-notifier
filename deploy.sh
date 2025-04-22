#!/bin/bash
# AWS Resource Notifier - CloudFormation Deployment Script

set -e

# Default values
AWS_REGION="eu-west-1"
ENVIRONMENT="aws-resource-notifier"
RESOURCE_PREFIX="aws-resource-notifier"
CREATE_CLOUDTRAIL="false"
TEAMS_WEBHOOK_URL=""

# Script usage
function show_usage {
  echo "AWS Resource Notifier - CloudFormation Deployment Script"
  echo ""
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -h, --help                 Show this help message"
  echo "  -r, --region REGION        AWS region to deploy regional services to [default: eu-west-1]"
  echo "  -e, --environment ENV      Environment (dev, test, prod) [default: dev]"
  echo "  -p, --prefix PREFIX        Resource prefix [default: aws-resource-notifier]"
  echo "  -w, --webhook-url URL      Microsoft Teams webhook URL"
  echo "  -d, --delete               Delete the CloudFormation stacks"
  echo ""
  echo "Examples:"
  echo "  $0 --region us-west-2 --webhook-url https://webhook-url"
  exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -h|--help)
      show_usage
      ;;
    -r|--region)
      AWS_REGION="$2"
      shift
      shift
      ;;
    -e|--environment)
      ENVIRONMENT="$2"
      shift
      shift
      ;;
    -p|--prefix)
      RESOURCE_PREFIX="$2"
      shift
      shift
      ;;
    -w|--webhook-url)
      TEAMS_WEBHOOK_URL="$2"
      shift
      shift
      ;;
    -d|--delete)
      DELETE="true"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      show_usage
      ;;
  esac
done

# Stack names for CloudFormation
GLOBAL_STACK_NAME="${RESOURCE_PREFIX}-global-stack"
REGIONAL_STACK_NAME="${RESOURCE_PREFIX}-regional-stack"

# Function to create Lambda deployment package
create_lambda_package() {
    local function_name=$1
    local source_file=$2
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local output_dir="${script_dir}/build"
    local package_file="${output_dir}/${function_name}.zip"
    
    echo "Creating package for ${function_name}..."
    echo "Script directory: ${script_dir}"
    echo "Output directory: ${output_dir}"
    echo "Source file: ${source_file}"
    echo "Package file: ${package_file}"
    
    # Create build directory if it doesn't exist
    mkdir -p "${output_dir}"
    
    # Create a temporary directory for packaging
    local temp_dir=$(mktemp -d)
    echo "Created temporary directory: ${temp_dir}"
    
    # Copy the Lambda function code
    if [ ! -f "${source_file}" ]; then
        echo "Error: Source file ${source_file} does not exist"
        rm -rf "${temp_dir}"
        exit 1
    fi
    
    cp "${source_file}" "${temp_dir}/"
    echo "Copied source file to temp directory"
    
    # Install dependencies if requirements.txt exists
    if [ -f "${script_dir}/requirements.txt" ]; then
        echo "Installing dependencies from requirements.txt..."
        pip install -r "${script_dir}/requirements.txt" -t "${temp_dir}"
    fi
    
    # Create ZIP file
    echo "Creating ZIP file..."
    cd "${temp_dir}"
    zip -r "${package_file}" .
    cd - > /dev/null
    
    # Verify ZIP file was created
    if [ ! -f "${package_file}" ]; then
        echo "Error: Failed to create ZIP file at ${package_file}"
        rm -rf "${temp_dir}"
        exit 1
    fi
    
    echo "Created ZIP file: ${package_file}"
    ls -l "${package_file}"
    
    # Clean up
    rm -rf "${temp_dir}"
    
    # Return the package file path
    echo "${package_file}"
}

# Function to create S3 bucket if it doesn't exist
create_s3_bucket() {
    local bucket_name=$1
    local region=$2
    
    if ! aws s3 ls "s3://${bucket_name}" 2>&1 > /dev/null; then
        echo "Creating S3 bucket ${bucket_name} in ${region}..."
        aws s3api create-bucket \
            --bucket "${bucket_name}" \
            --region "${region}" \
            --create-bucket-configuration LocationConstraint="${region}"
        
        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket "${bucket_name}" \
            --versioning-configuration Status=Enabled
    else
        echo "S3 bucket ${bucket_name} already exists"
    fi
}

# Check if we're deleting the stacks
if [[ "${DELETE}" == "true" ]]; then
  echo "Deleting CloudFormation stacks..."
  
  # Delete regional stack
  echo "Deleting regional stack in ${AWS_REGION}..."
  aws cloudformation delete-stack \
    --stack-name "${REGIONAL_STACK_NAME}" \
    --region "${AWS_REGION}"
  
  # Delete global stack in us-east-1
  echo "Deleting global stack in us-east-1..."
  aws cloudformation delete-stack \
    --stack-name "${GLOBAL_STACK_NAME}" \
    --region "us-east-1"
  
  echo "Stack deletion initiated. Please check AWS Console for status."
  exit 0
fi

# Create S3 bucket for Lambda code
LAMBDA_BUCKET_NAME="${RESOURCE_PREFIX}-lambda-code-${ENVIRONMENT}"
create_s3_bucket "${LAMBDA_BUCKET_NAME}" "${AWS_REGION}"

# Create Lambda deployment packages
echo "Creating Lambda deployment packages..."
echo "Current directory: $(pwd)"
echo "Script directory: $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create packages and store their paths
RESOURCE_NOTIFIER_PACKAGE=$(create_lambda_package "resource_creation_notifier" "src/lambda/resource_creation_notifier.py")
DELETION_NOTIFIER_PACKAGE=$(create_lambda_package "resource_deletion_notifier" "src/lambda/resource_deletion_notifier.py")

# Verify packages were created
echo "Checking package files..."
echo "Resource notifier package: ${RESOURCE_NOTIFIER_PACKAGE}"
echo "Deletion notifier package: ${DELETION_NOTIFIER_PACKAGE}"

# Convert to absolute paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESOURCE_NOTIFIER_PACKAGE="${SCRIPT_DIR}/build/resource_creation_notifier.zip"
DELETION_NOTIFIER_PACKAGE="${SCRIPT_DIR}/build/resource_deletion_notifier.zip"

if [ ! -f "${RESOURCE_NOTIFIER_PACKAGE}" ] || [ ! -f "${DELETION_NOTIFIER_PACKAGE}" ]; then
    echo "Error: Failed to create one or more Lambda packages"
    echo "Directory contents:"
    ls -la "${SCRIPT_DIR}/build/"
    exit 1
fi

# Upload Lambda code to S3
echo "Uploading Lambda code to S3..."
aws s3 cp "${RESOURCE_NOTIFIER_PACKAGE}" "s3://${LAMBDA_BUCKET_NAME}/resource_creation_notifier.zip"
aws s3 cp "${DELETION_NOTIFIER_PACKAGE}" "s3://${LAMBDA_BUCKET_NAME}/resource_deletion_notifier.zip"

# Deploy regional services stack
echo "Deploying regional services stack to ${AWS_REGION}..."
aws cloudformation deploy \
  --template-file cloudformation/regional-services.yaml \
  --stack-name "${REGIONAL_STACK_NAME}" \
  --region "${AWS_REGION}" \
  --parameter-overrides \
    ResourcePrefix="${RESOURCE_PREFIX}" \
    Environment="${ENVIRONMENT}" \
    CreateCloudTrail="false" \
    TeamsWebhookUrl="${TEAMS_WEBHOOK_URL}" \
    LambdaCodeBucket="${LAMBDA_BUCKET_NAME}" \
  --capabilities CAPABILITY_NAMED_IAM

# Deploy global services stack
echo "Deploying global services stack to us-east-1..."
aws cloudformation deploy \
  --template-file cloudformation/global-services.yaml \
  --stack-name "${GLOBAL_STACK_NAME}" \
  --region "us-east-1" \
  --parameter-overrides \
    ResourcePrefix="${RESOURCE_PREFIX}" \
    Environment="${ENVIRONMENT}" \
    TeamsWebhookUrl="${TEAMS_WEBHOOK_URL}" \
    LambdaCodeBucket="${LAMBDA_BUCKET_NAME}" \
  --capabilities CAPABILITY_NAMED_IAM

echo "Deployment completed successfully!" 