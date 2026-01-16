# Azure Functions Backend

HTTP API backend for the Healthcare Graph Agent. Exposes tool endpoints that query the Cosmos DB graph database.

## Prerequisites

- Azure CLI (`az`) installed and logged in
- Azure Functions Core Tools v4 (`func`)
- Python 3.11+

## Deployment

### Option 1: Using deploy script (Recommended)

```bash
cd azure-functions
./deploy-azure.sh
```

The script automatically:
1. Creates/updates Azure resources (Storage Account, Function App)
2. Copies required directories from project root (`src/`, `config/`)
3. Publishes to Azure

### Option 2: Manual deployment

If deploying without the script (e.g., CI/CD, different host), you must copy the shared directories first:

```bash
cd azure-functions

# Required: Copy shared modules and config
cp -r ../src ./src
cp -r ../config ./config

# Then publish
func azure functionapp publish <your-function-app-name>
```

### Option 3: Using Makefile

From the project root:

```bash
make deploy-azure
```

## Required Directory Structure

After copying, your `azure-functions/` directory should contain:

```
azure-functions/
├── function_app.py
├── requirements.txt
├── host.json
├── src/                    ← Copied from project root
│   ├── core/
│   │   ├── tool_registry.py
│   │   ├── cosmos_connection.py
│   │   └── exceptions.py
│   └── domains/
│       └── referral_network/
│           └── tools.py
└── config/                 ← Copied from project root
    └── domains.yaml
```

**Important:** The `src/` and `config/` directories are gitignored because they're copies. Always copy fresh from the project root before deploying.

## Environment Variables

Configure these in Azure Portal → Function App → Configuration → Application Settings:

| Variable | Description | Example |
|----------|-------------|---------|
| `COSMOS_ACCOUNT_NAME` | Cosmos DB account name | `cosmos-referral-demo-xxx` |
| `COSMOS_PRIMARY_KEY` | Cosmos DB primary key | `abc123...` |
| `COSMOS_DATABASE` | Database name | `referral-network` |
| `COSMOS_GRAPH` | Graph/container name | `hospital-graph` |

## Local Development

1. Copy the shared directories:
   ```bash
   cp -r ../src ./src
   cp -r ../config ./config
   ```

2. Create `local.settings.json` from the example:
   ```bash
   cp local.settings.json.example local.settings.json
   # Edit with your Cosmos DB credentials
   ```

3. Run locally:
   ```bash
   func start
   ```

4. Test the health endpoint:
   ```bash
   curl http://localhost:7071/api/health
   ```

## Troubleshooting

### "Configuration file not found" error
The `config/domains.yaml` file wasn't copied. Run:
```bash
cp -r ../config ./config
```

### "No module named 'yaml'" error
PyYAML is missing. Ensure `requirements.txt` includes `PyYAML>=6.0` and redeploy.

### "No module named 'src.core'" error
The `src/` directory wasn't copied. Run:
```bash
cp -r ../src ./src
```

### Functions return 404
Check Azure Functions logs for import errors:
```bash
func azure functionapp logstream <your-function-app-name>
```
