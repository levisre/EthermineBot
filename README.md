# EthermineBot
My Tiny Telegram bot to monitor ETH Miner and Polygon Wallet. Written in Python 3

# Usage:

Better run it with `venv`.

Install dependencies: 

```bash
pip install -r requirement.txt
```

Open `setting.json`, and fill out the necessary values:

| Value | Meaning |
|-------|-----------|
| `tg_bot_token` | Your personal Telegram bot token, register one via `@botfather`[How-to](https://core.telegram.org/bots) |
| `target_wallet` | Your miner address also your wallet address (without `0x` prefix) |
| `polygon_token` | Use to track your wallet balance at `polygonscan.com`, if you're setting your payout via Polygon Network | 
| `target_contract` | The contract address of your token which you want to monitor. For e.g, Contract address of Wrapped ETH (WETH) is `0x7ceb23fd6bc0add59e62ac25578270cff1b9f619` |

Run the bot: `python bot.py`

Then open Telegram and search for your bot name (registered when getting token from `@botfather`), start chat and send commands:

| Command | Meaning |
|---------|---------|
| `/start` | Just say a hello sentence to ensure that the bot is working |
| `/status` | Show current status of the miner at `ethermine.com`: active workers, current hashrate, reported hashrate, unpaid balance (ETH & USDT), network difficulty) |
| `/balance` | Show current balance of the wallet: Current ETH amount, Current ETH/USDT exchange rate, Current USDT amount |
