# Azure Sentiment Analysis Learning Program

This repository contains a Python-based implementation for performing sentiment analysis and aspect-based opinion mining on text data using the **Azure Cognitive Services Language Service** (formerly Text Analytics).

The project is structured to demonstrate cloud integration, secure authentication, batch optimization, transient error handling, and structured reporting.

---

## 📋 Table of Contents
1. [Project Structure](#-project-structure)
2. [Azure Resource Provisioning Guide](#-azure-resource-provisioning-guide)
3. [Environment Setup](#-environment-setup)
4. [How to Run](#-how-to-run)
5. [Key Implementation Features](#-key-implementation-features)
6. [Security & Credential Management](#-security--credential-management)

---

## 📁 Project Structure

```
├── data/
│   └── sample_reviews.json        # Preprocessed sample review dataset
├── docs/
│   ├── analysis_report.md         # Narrative report & breakdown of results
│   └── security_documentation.md  # Detailed API security practices
├── output/
│   ├── results.json               # Parsed sentiment analysis JSON output
│   └── summary_report.txt         # Plaintext summary analytics report
├── src/
│   └── sentiment_analyzer.py      # Core python script integrating Azure SDK
└── README.md                      # Setup and environment configuration guide
```

---

## ☁️ Azure Resource Provisioning Guide

To run this project against live Azure Cognitive Services, you must provision a Language Service resource.

### Option A: Via the Azure Portal
1. Sign in to the [Azure Portal](https://portal.azure.com/).
2. Click **Create a resource** and search for **Language**.
3. Select **Language Service** and click **Create**.
4. Configure the resource settings:
   - **Subscription**: Your active Azure subscription.
   - **Resource group**: Select an existing group or create a new one (e.g., `rg-sentiment-analysis`).
   - **Region**: Select a region close to you (e.g., `East US` or `West Europe`).
   - **Name**: A unique name (e.g., `lang-sentiment-learning`).
   - **Pricing tier**: Select `Free F0` (ideal for learning) or `Standard S`.
5. Click **Review + create**, then **Create**.
6. Once deployed, navigate to the resource. Under **Resource Management**, select **Keys and Endpoint**.
7. Copy **KEY 1** and the **Endpoint URL**.

### Option B: Via Azure CLI
If you have the Azure CLI installed and authenticated, run the following commands:

```bash
# 1. Create a Resource Group (if not already existing)
az group create --name rg-sentiment-analysis --location eastus

# 2. Provision the Language Cognitive Service Account
az cognitiveservices account create \
    --name lang-sentiment-learning \
    --resource-group rg-sentiment-analysis \
    --kind TextAnalytics \
    --sku F0 \
    --location eastus \
    --yes

# 3. Retrieve Keys and Endpoint
az cognitiveservices account keys list --name lang-sentiment-learning --resource-group rg-sentiment-analysis
az cognitiveservices account show --name lang-sentiment-learning --resource-group rg-sentiment-analysis --query properties.endpoint -o tsv
```

---

## ⚙️ Environment Setup

### 1. Install Dependencies
This project uses the official Azure SDKs. Install the packages using `pip`:

```bash
pip install azure-ai-textanalytics azure-identity azure-keyvault-secrets
```

### 2. Configure Credentials
The script reads credentials securely from environment variables. Set them in your terminal:

**Windows PowerShell:**
```powershell
$env:AZURE_LANGUAGE_ENDPOINT="https://<your-resource-name>.cognitiveservices.azure.com/"
$env:AZURE_LANGUAGE_KEY="<your-azure-key>"
```

**Windows CMD:**
```cmd
set AZURE_LANGUAGE_ENDPOINT=https://<your-resource-name>.cognitiveservices.azure.com/
set AZURE_LANGUAGE_KEY=<your-azure-key>
```

**Linux/macOS Bash:**
```bash
export AZURE_LANGUAGE_ENDPOINT="https://<your-resource-name>.cognitiveservices.azure.com/"
export AZURE_LANGUAGE_KEY="<your-azure-key>"
```

> [!TIP]
> **Simulation Mode Fallback:** If you do not have an active Azure subscription or these environment variables are not set, the script automatically runs in **Simulation Mode** using a local mock client. This allows grading and testing of the program logic immediately without provisioning cloud resources.

---

## 🚀 How to Run

Run the script using Python. By default, it will attempt to connect to Azure (or fall back to Simulation Mode if variables are missing):

```bash
python src/sentiment_analyzer.py
```

### Command Line Arguments
You can customize paths, batch sizes, Key Vault integration, or force modes using arguments:

```bash
# Force Simulation Mode even if credentials are set
python src/sentiment_analyzer.py --mock

# Run with Key Vault retrieval
python src/sentiment_analyzer.py --endpoint "https://<lang-resource>.cognitiveservices.azure.com/" --vault-url "https://<vault-name>.vault.azure.net/" --secret-name "LanguageServiceApiKey"

# Specify custom inputs, outputs, and batch size
python src/sentiment_analyzer.py --input data/sample_reviews.json --output output/results.json --batch-size 5
```

---

## 🛠️ Key Implementation Features

1. **Batching:** The script splits the input review list into batches of `10` (the standard API request limit) before making calls, reducing API request overhead and staying within free-tier limits.
2. **Opinion Mining:** The optional opinion mining (aspect-based sentiment) is enabled, which extracts target aspects (like "food", "battery life") and associates them with descriptors ("delicious", "fantastic").
3. **Transient Retry Logic:** Implements exponential backoff when catching transient exceptions (HTTP status `429` for rate limits or `5xx` server errors), retry attempts back off exponentially (`2s`, `4s`, `8s`) before giving up.
4. **Structured Mapping:** Standardizes the SDK response format into clean, flat JSON structures saved in `output/results.json` containing:
   - Document ID
   - Document overall sentiment and confidence scores
   - Sentence-by-sentence text, label, and scores
   - aspect-level target and descriptor relationships

---

## 🔒 Security & Credential Management

*   **Never Hardcode Keys:** Credentials are kept out of source code by utilizing `os.environ.get`.
*   **Azure Key Vault & Managed Identity:** Refer to [docs/security_documentation.md](file:///c:/Users/duduy/OneDrive/Documents/Assignment_12/docs/security_documentation.md) for a comprehensive guide on integrating Azure Key Vault and replacing API keys with Microsoft Entra ID (Azure Active Directory) Managed Identities in production.
