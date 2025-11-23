# FactFlow Setup Guide

This guide provides detailed instructions for setting up and running the FactFlow agent system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Operating System**: Windows, macOS, or Linux
- **Internet Connection**: Required for API calls and Google Search

### Required Accounts

1. **Google AI Studio Account**
   - Sign up at [Google AI Studio](https://aistudio.google.com/)
   - Generate an API key from the [API Keys page](https://aistudio.google.com/app/api-keys)

2. **Optional: Alpha Vantage Account** (for enhanced sentiment data)
   - Sign up at [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
   - Get a free API key (500 API calls per day)

## Installation

### Step 1: Clone or Download the Project

If you have the project in a repository:
```bash
git clone <repository-url>
cd factflow
```

Or if you have the project files locally, navigate to the `factflow` directory.

### Step 2: Create a Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `google-adk` - Agent Development Kit
- `google-generativeai` - Gemini API client
- `yfinance` - Stock market data
- `requests` - HTTP library
- `python-dotenv` - Environment variable management
- `pandas` - Data manipulation
- `numpy` - Numerical computing

### Step 4: Set Up Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:
```env
GEMINI_API_KEY=your_gemini_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here  # Optional
```

**Important**: Never commit your `.env` file to version control. It's already in `.gitignore`.

### Step 5: Create Logs Directory

```bash
mkdir logs
```

This directory will store log files, traces, and metrics.

## Configuration

### Model Selection

By default, FactFlow uses `gemini-2.5-flash-lite` for cost efficiency. You can change this in:

- `agents/sentiment_agents.py` - Change `model_name` parameter
- `main.py` - Pass different model name to `FactFlowSessionManager`

Available models:
- `gemini-2.5-flash-lite` (default, fastest, cost-effective)
- `gemini-2.0-flash-exp` (balanced)
- `gemini-1.5-pro` (most capable, higher cost)

### Logging Configuration

Edit `observability/logging_config.py` to customize logging:

```python
# Change log level
logger = setup_logging(log_level="DEBUG")  # DEBUG, INFO, WARNING, ERROR

# Add file logging
logger = setup_logging(log_file="logs/factflow.log")
```

### Memory Bank Configuration

The Memory Bank stores historical analyses in `factflow_memory.json`. To change the location:

```python
from factflow.session.memory_service import MemoryBank

memory = MemoryBank(storage_path="custom_path.json")
```

## Verification

### Test Installation

Run a simple test to verify everything is set up correctly:

```python
# test_setup.py
import os
from dotenv import load_dotenv

load_dotenv()

# Check API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found in .env file")
else:
    print("✅ GEMINI_API_KEY found")

# Test imports
try:
    from google.adk.agents import LlmAgent
    print("✅ google-adk imported successfully")
except ImportError as e:
    print(f"❌ Failed to import google-adk: {e}")

try:
    import yfinance as yf
    print("✅ yfinance imported successfully")
except ImportError as e:
    print(f"❌ Failed to import yfinance: {e}")

try:
    from factflow.tools.market_tools import get_crypto_price_data
    print("✅ FactFlow tools imported successfully")
except ImportError as e:
    print(f"❌ Failed to import FactFlow tools: {e}")

print("\n✅ Setup verification complete!")
```

Run it:
```bash
python test_setup.py
```

### Test Market Tools

Test the market data tools independently:

```python
# test_tools.py
from factflow.tools.market_tools import get_crypto_price_data, get_stock_data

# Test crypto data
result = get_crypto_price_data("ethereum")
print("Crypto Data:", result)

# Test stock data
result = get_stock_data("AAPL")
print("Stock Data:", result)
```

Run it:
```bash
python test_tools.py
```

### Test Agent System

Run a simple agent query:

```bash
python -m factflow.main "Test query: What is Bitcoin?"
```

## Troubleshooting

### Common Issues

#### 1. "GEMINI_API_KEY not found"

**Solution**: 
- Make sure you created a `.env` file in the `factflow` directory
- Verify the key is correctly formatted (no quotes, no spaces)
- Check that `python-dotenv` is installed: `pip install python-dotenv`

#### 2. "ModuleNotFoundError: No module named 'google.adk'"

**Solution**:
```bash
pip install google-adk
```

If that doesn't work, try:
```bash
pip install --upgrade google-adk
```

#### 3. "429 Too Many Requests" Error

**Solution**:
- You've hit the API rate limit
- Wait a few minutes and try again
- Consider using a different API key or upgrading your quota

#### 4. "Asset not found" Error

**Solution**:
- For crypto: Use full names (e.g., "ethereum" not "ETH")
- For stocks: Use ticker symbols (e.g., "AAPL" not "Apple")
- Check the asset name spelling

#### 5. Import Errors

**Solution**:
- Make sure you're in the correct directory
- Activate your virtual environment
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

#### 6. "Connection timeout" Errors

**Solution**:
- Check your internet connection
- CoinGecko API might be temporarily unavailable
- Try again after a few minutes

### Getting Help

1. **Check Logs**: Look in the `logs/` directory for detailed error messages
2. **Enable Debug Logging**: Set `log_level="DEBUG"` in logging configuration
3. **Course Discord**: Ask questions on the Kaggle Discord server
4. **GitHub Issues**: Create an issue in the repository (if applicable)

### Performance Tips

1. **Use Faster Models**: `gemini-2.5-flash-lite` is faster and cheaper than `gemini-1.5-pro`
2. **Cache Results**: The Memory Bank stores previous analyses to avoid redundant API calls
3. **Batch Queries**: Process multiple assets in a single session when possible

## Next Steps

Once setup is complete:

1. Read [USAGE.md](USAGE.md) to learn how to use FactFlow
2. Check out the demo notebook in `notebooks/`
3. Review [SUBMISSION.md](SUBMISSION.md) for capstone submission guidelines

## Additional Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [CoinGecko API Documentation](https://www.coingecko.com/en/api)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)

