# Farabixo API Request Sender

High-performance concurrent request sender for Farabixo API—streamlined bulk order execution with configurable rate limiting and detailed reporting.

## Features

- Concurrent multi-threaded request dispatch
- Configurable rate limiting and request throttling
- Automatic error handling and timeout management
- Real-time execution metrics and reporting
- Results export to timestamped log files
- Secure credential management via environment variables

## Prerequisites

- Python 3.7+
- pip package manager

## Setup

### 1. Initialize Configuration

Copy the example environment file:

``ash
cp .env.example .env
``

### 2. Configure Environment Variables

Edit .env with your credentials and order parameters:

``env
API_TOKEN=your_bearer_token_here
INSTRUMENT_IDENTIFICATION=IRO3PRIZ0001
ORDER_SIDE=1
QUANTITY=1289
PRICE=29900
``

**Note:** .env is gitignored and never committed.

### 3. Install Dependencies

``ash
pip install -r requirements.txt
``

## Usage

``ash
python fara.py
``

### Configuration Prompt

The application will prompt for execution parameters:

``
============================================================
       Concurrent Request Sender - Configuration
============================================================

📊 Main Settings:
----------------------------------------
🔢 Total number of requests (e.g., 100): 50
⚡ Request rate (requests per second) - 0 for unlimited (e.g., 10): 10
🧵 Number of concurrent threads (e.g., 20): 5
⏱️ Request timeout (seconds) - e.g., 5: 10

🎯 Advanced Settings:
----------------------------------------
📝 Show detailed output for each request? (y/n) - default: n: n
💾 Save results to file? (y/n) - default: n: y
``

## Project Structure

``
.
├── fara.py                 # Main application
├── config.py               # Configuration module
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── .env                    # Local credentials (gitignored)
└── README.md               # This file
``

## Environment Variables

| Variable | Description |
|----------|-------------|
| API_URL | API endpoint (default: https://gateway.example.com/api/v2/orders) |
| API_TOKEN | Bearer token for authentication |
| INSTRUMENT_IDENTIFICATION | Trading instrument ID (default: IRO3PRIZ0001) |
| ORDER_SIDE | Order direction: 1 (buy) or -1 (sell) |
| QUANTITY | Order quantity |
| PRICE | Order price per unit |

## Execution Parameters

- **Total requests**: Number of API calls to dispatch
- **Request rate**: Requests per second (0 = unlimited)
- **Concurrent threads**: Number of parallel workers
- **Request timeout**: Per-request timeout in seconds
- **Show details**: Enable verbose per-request output
- **Save results**: Export summary to timestamped file

## Results

Upon completion, you receive a summary report:

``
============================================================
📊 Final Report:
============================================================
   ✅ Successful requests (200): 45
   ❌ Failed requests: 5
   🚫 Rate limited (429): 2
   ⌛ Timeouts: 3
   📈 Actual rate: 8.33 requests/second
   ⏱️ Total time: 6.00 seconds
   📊 Success rate: 90.0%
============================================================

💾 Results saved to 'result_20260616_153045.txt'
``

## Troubleshooting

### "API_TOKEN not found"
Verify .env file exists and API_TOKEN is set correctly.

### "429 Rate Limit"
Reduce request rate or decrease concurrent threads.

### Timeout Errors
Increase timeout duration or verify network connectivity.

## Security

- Store all credentials in .env, never in code
- Never commit .env to version control
- Use strong, unique API tokens
- Rotate tokens regularly

## License

MIT

## Support

Open an issue for questions or bug reports.
