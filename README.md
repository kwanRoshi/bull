# Crypto Market Bot

An Eliza-powered Twitter bot that monitors OKX DEX cryptocurrency markets and posts automated analysis using AI.

## Features

- Real-time monitoring of OKX DEX markets
- Automated market analysis using GPT-4 and Claude
- Regular Twitter updates with market insights
- Technical analysis and market strength indicators
- Support for multiple trading pairs (BTC, ETH, ARB, MATIC, OP)

## Prerequisites

- Node.js 23+
- npm/pnpm
- Python 3.8+
- Eliza CLI (`npm install -g @elizaos/cli`)

## Setup

1. Clone this repository:
```bash
git clone <your-repo-url>
cd <repo-directory>
```

2. Create a `.env` file with your API keys:
```bash
cp .env.example .env
```

Fill in the following credentials in `.env`:
- Twitter API credentials
- OKX API credentials
- OpenAI API key
- Anthropic API key

3. Make the start script executable:
```bash
chmod +x start.sh
```

4. Start the bot:
```bash
./start.sh
```

## Configuration

You can customize the bot's behavior by editing `crypto_bot.json`:

- Modify trading pairs in `data_sources.okx.pairs`
- Adjust posting interval in `features.twitter.post_interval`
- Customize AI prompts in the `prompts` section
- Configure different AI models in the `models` section

## Monitoring

The bot will:
- Fetch market data every 5 minutes
- Post analysis every 4 hours
- Log all activities to the console
- Handle API errors gracefully

## Note

Make sure to comply with:
- Twitter's automation rules
- OKX API rate limits
- AI API usage limits 