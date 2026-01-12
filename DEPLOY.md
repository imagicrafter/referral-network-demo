# Deployment Guide

This guide covers deploying the full architecture:
1. **Azure Functions** - Backend API that queries Cosmos DB
2. **DO ADK Agent** - LLM agent that calls the backend API
3. **Open WebUI** - Frontend that connects via the DO Function Pipe

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Open WebUI    │────▶│  DO ADK Agent   │────▶│ Azure Functions │────▶│  Cosmos DB      │
│   (Frontend)    │     │  (LLM + Tools)  │     │  (Backend API)  │     │  (Graph DB)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
       │                        │                       │
       │                        │                       │
  do-function-pipe.py    Gradient Platform      Your Azure account
```

## Step 1: Deploy Azure Functions Backend

### Prerequisites

- Azure CLI installed (`brew install azure-cli` on macOS)
- Azure account with subscription

### Create Azure Function App

```bash
# Login to Azure
az login

# Create resource group (if needed)
az group create --name referral-network-rg --location eastus

# Create storage account (required for Functions)
az storage account create \
  --name referralnetworkstorage \
  --resource-group referral-network-rg \
  --location eastus \
  --sku Standard_LRS

# Create Function App
az functionapp create \
  --name referral-network-api \
  --resource-group referral-network-rg \
  --storage-account referralnetworkstorage \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux
```

### Configure Environment Variables

```bash
# Set Cosmos DB connection settings
az functionapp config appsettings set \
  --name referral-network-api \
  --resource-group referral-network-rg \
  --settings \
    COSMOS_ACCOUNT_NAME=your-cosmos-account \
    COSMOS_PRIMARY_KEY=your-cosmos-key \
    COSMOS_DATABASE=referral-network \
    COSMOS_GRAPH=hospital-graph
```

### Deploy the Functions

```bash
cd azure-functions

# Create local.settings.json from example
cp local.settings.json.example local.settings.json
# Edit local.settings.json with your Cosmos DB credentials

# Deploy to Azure
func azure functionapp publish referral-network-api
```

### Get the Function URL and Key

```bash
# Get the function URL
az functionapp show \
  --name referral-network-api \
  --resource-group referral-network-rg \
  --query defaultHostName \
  --output tsv

# Get the function key
az functionapp keys list \
  --name referral-network-api \
  --resource-group referral-network-rg \
  --query functionKeys \
  --output tsv
```

Note these values - you'll need them for the DO ADK agent.

### Test the Backend API

```bash
# Test health endpoint
curl https://referral-network-api.azurewebsites.net/api/health

# Test a tool endpoint (with function key)
curl -X POST https://referral-network-api.azurewebsites.net/api/tools/get_network_statistics \
  -H "Content-Type: application/json" \
  -H "x-functions-key: YOUR_FUNCTION_KEY" \
  -d '{}'
```

## Step 2: Deploy DO ADK Agent

### Update Configuration

Edit `gradient-agents/.env`:

```bash
# Gradient Configuration
DIGITALOCEAN_API_TOKEN=your-do-token
GRADIENT_MODEL_ACCESS_KEY=your-gradient-key
GRADIENT_MODEL=openai-gpt-oss-120b

# Backend API Configuration (from Step 1)
BACKEND_API_URL=https://referral-network-api.azurewebsites.net
BACKEND_API_KEY=your-function-key
```

### Deploy to Gradient

```bash
cd gradient-agents

# Load environment variables
source .env

# Deploy
gradient agent deploy
```

Note the agent URL returned (e.g., `https://referral-network-agent.agents.do-ai.run`)

### Test the Agent

```bash
curl -X POST https://referral-network-agent.agents.do-ai.run/api/v1/chat/completions \
  -H "Authorization: Bearer $GRADIENT_MODEL_ACCESS_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Give me an overview of the referral network"}],
    "stream": false
  }'
```

## Step 3: Configure Open WebUI

### Install the DO Function Pipe

1. Go to Open WebUI → Admin → Functions
2. Create a new function and paste the contents of `pipes/do-function-pipe.py`
3. Configure the valves:
   - `DIGITALOCEAN_FUNCTION_URL`: Your agent URL (e.g., `https://referral-network-agent.agents.do-ai.run`)
   - `DIGITALOCEAN_FUNCTION_TOKEN`: Your Gradient model access key
   - `ENABLE_STREAMING`: true
   - `DEBUG_MODE`: false (set to true for troubleshooting)

### Select the Pipe as Your Model

1. Go to Settings → Interface
2. Set "Task Model" to the DO Function Pipe
3. In a chat, select the DO Function Pipe as your model

## Troubleshooting

### Azure Functions Issues

**Check function logs:**
```bash
az functionapp log deployment show \
  --name referral-network-api \
  --resource-group referral-network-rg
```

**Check application logs:**
```bash
az monitor app-insights query \
  --app referral-network-api \
  --analytics-query "traces | order by timestamp desc | take 50"
```

### DO ADK Agent Issues

**Check agent status:**
```bash
gradient agent status
```

**View agent logs:**
```bash
gradient agent logs
```

### Connection Issues

1. Verify Azure Functions are accessible:
   ```bash
   curl https://your-function-app.azurewebsites.net/api/health
   ```

2. Verify DO agent can reach Azure:
   - Check BACKEND_API_URL is correct
   - Check BACKEND_API_KEY is correct

3. Check Cosmos DB connectivity:
   - Ensure firewall allows Azure Functions IP
   - Verify connection string is correct

## Cost Considerations

| Service | Pricing Model | Estimated Cost |
|---------|--------------|----------------|
| Azure Functions (Consumption) | Pay per execution | ~$0.20 per million executions |
| Cosmos DB | RU/s + Storage | Varies by usage |
| Gradient Agent | Pay per request | See DO pricing |

## Security Notes

1. **API Keys**: Never commit `.env` files with real keys
2. **Azure Functions**: Use function-level auth keys
3. **Cosmos DB**: Use managed identity in production
4. **Network**: Consider VNet integration for production
