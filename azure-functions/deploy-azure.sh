#!/bin/bash
# Deploy Azure Functions backend for Referral Network API

set -e  # Exit on error

RESOURCE_GROUP="rg-referral-network-demo"
LOCATION="centralus"
STORAGE_ACCOUNT="referralnetstr$RANDOM"
FUNCTION_APP="referral-network-api"
SUBSCRIPTION="d79c8344-ab62-4fa6-8883-cca9ebd92d7b"

echo "=== Deploying Azure Functions Backend ==="
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Subscription: $SUBSCRIPTION"
echo ""

# Check if logged in to Azure
echo "Checking Azure login..."
az account show > /dev/null 2>&1 || { echo "Please run 'az login' first"; exit 1; }

# Set subscription explicitly
echo "Setting subscription..."
az account set --subscription "$SUBSCRIPTION"

# Create storage account
echo "Creating storage account: $STORAGE_ACCOUNT..."
az storage account create \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --subscription "$SUBSCRIPTION" \
  --only-show-errors || echo "Storage account may already exist, continuing..."

# Create Function App
echo "Creating Function App: $FUNCTION_APP..."
az functionapp create \
  --name "$FUNCTION_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --storage-account "$STORAGE_ACCOUNT" \
  --consumption-plan-location "$LOCATION" \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux \
  --subscription "$SUBSCRIPTION" \
  --only-show-errors || echo "Function App may already exist, continuing..."

# Wait for Function App to be ready
echo "Waiting for Function App to be ready..."
sleep 10

# Set Cosmos DB environment variables
echo ""
echo "=== Configuring Cosmos DB Connection ==="
echo "Please enter your Cosmos DB settings (or press Enter to skip):"

read -p "COSMOS_ACCOUNT_NAME: " COSMOS_ACCOUNT
read -p "COSMOS_PRIMARY_KEY: " COSMOS_KEY
read -p "COSMOS_DATABASE [referral-network]: " COSMOS_DB
COSMOS_DB=${COSMOS_DB:-referral-network}
read -p "COSMOS_GRAPH [hospital-graph]: " COSMOS_GRAPH
COSMOS_GRAPH=${COSMOS_GRAPH:-hospital-graph}

if [ -n "$COSMOS_ACCOUNT" ] && [ -n "$COSMOS_KEY" ]; then
  echo "Setting Cosmos DB configuration..."
  az functionapp config appsettings set \
    --name "$FUNCTION_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
      COSMOS_ACCOUNT_NAME="$COSMOS_ACCOUNT" \
      COSMOS_PRIMARY_KEY="$COSMOS_KEY" \
      COSMOS_DATABASE="$COSMOS_DB" \
      COSMOS_GRAPH="$COSMOS_GRAPH" \
    --only-show-errors
else
  echo "Skipping Cosmos DB configuration. Set it later in Azure Portal."
fi

# Copy shared src/ directory for deployment
echo ""
echo "=== Preparing Deployment Package ==="
echo "Copying shared src/ directory..."
cp -r ../src ./src
echo "src/ directory copied successfully"

# Publish the functions
echo ""
echo "=== Publishing Functions ==="
func azure functionapp publish "$FUNCTION_APP"

# Get the function URL
echo ""
echo "=== Deployment Complete ==="
FUNCTION_URL=$(az functionapp show --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" --query defaultHostName --output tsv)
echo "Function App URL: https://$FUNCTION_URL"

# Get function key
echo ""
echo "Getting function key..."
FUNCTION_KEY=$(az functionapp keys list --name "$FUNCTION_APP" --resource-group "$RESOURCE_GROUP" --query functionKeys.default --output tsv 2>/dev/null || echo "")

if [ -n "$FUNCTION_KEY" ]; then
  echo "Function Key: $FUNCTION_KEY"
  echo ""
  echo "Add these to your .env file:"
  echo "BACKEND_API_URL=https://$FUNCTION_URL"
  echo "BACKEND_API_KEY=$FUNCTION_KEY"
else
  echo "Could not retrieve function key. Get it from Azure Portal."
fi

echo ""
echo "Test the health endpoint:"
echo "curl https://$FUNCTION_URL/api/health"
