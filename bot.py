import requests
import json
import logging
import os
import sys
import argparse

from telegram.ext import Updater
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext.filters import Filters


ETHERMINE_API_URI = "https://api.ethermine.org"

POLYGON_API_URI = "https://api.polygonscan.com/api"

DEFAULT_CONFIG_FILE = "setting.json"


logging.basicConfig(level=logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


# Send request to server
def make_request(uri, header=None, data = None):
    response = requests.get(uri, headers=header if header is not None else None, data=data if data is not None else None)
    if response.status_code == 200:
        return response.content
    else:
        return None


def parse_args(argv):
    parser = argparse.ArgumentParser(description="EthermineBot", conflict_handler="resolve")
    parser.add_argument("--config", "-c", action="store", dest="config_path", help="path to config file", default=DEFAULT_CONFIG_FILE)
    args = parser.parse_args(argv)
    return args

class EthermineBot:
    bot_updater = None
    TELEGRAM_BOT_TOKEN = ""
    TARGET_WALLET = ""
    TARGET_CONTRACT = ""
    POLYGON_TOKEN = ""
    config_status = False
    def __init__(self):
        pass

    def __init__(self,config_file=DEFAULT_CONFIG_FILE):
        self.config_status = self.read_config(config_file)

    # Load Config from filename
    def read_config(self, filename=DEFAULT_CONFIG_FILE):
        if os.path.isfile(filename):
            try: 
                config_blob = json.load(open(filename))
                self.TELEGRAM_BOT_TOKEN = config_blob["setting"]["tg_bot_token"].strip()
                self.TARGET_WALLET = config_blob["setting"]["target_wallet"].strip()
                self.POLYGON_TOKEN = config_blob["setting"]["polygon_token"].strip()
                self.TARGET_CONTRACT = config_blob["setting"]["target_contract"].strip()
                logger.info("Config loaded. File name: %s, Target Wallet: %s, Target Contract: %s", filename, self.TARGET_WALLET, self.TARGET_CONTRACT)
                return True
            except Exception as e:
                logger.fatal("Config file load failed. Error: " + str(e))
                return False
        else:
            return False


    # Register bot and add command handler for bot
    def setup_bot(self):
 
        self.bot_updater = Updater(self.TELEGRAM_BOT_TOKEN, use_context=True)
        dispatcher = self.bot_updater.dispatcher
        start_handler = CommandHandler("start", self.start_handle)
        unknown_handler = MessageHandler(Filters.command, self.unknown)
        status_handler = CommandHandler("status", self.status_cmd)
        balance_handler = CommandHandler("balance", self.balance)
        dispatcher.add_handler(status_handler)
        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(balance_handler)
        dispatcher.add_handler(unknown_handler)

    def run(self):
        if self.config_status:
            if self.bot_updater is None:
                self.setup_bot()
            self.bot_updater.start_polling()
            self.bot_updater.idle()

    # Say Hello to ensure that the bot is up and running
    def start_handle(self, update: Update, context: CallbackContext):
        context.bot.send_message(chat_id= update.effective_chat.id, text = "Hello, I'm a bot and i'm working")


    # Unknown commands
    def unknown(self, update: Update, context: CallbackContext):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


    # Miner Status command
    def status_cmd(self, update: Update, context: CallbackContext):
        currentHashRate, reportedHashRate, activeWorkers, unpaid = self.get_miner_info()
        pool_diff = self.get_pool_status()
        usd_price = self.get_exchange_rate()
        message = "Current Hash Rate: %.2f MH/s\nReported Hash Rate: %.2f MH/s\nActive Worker: %d\nUnpaid Value (ETH): %.8f\nUnpaid Value (USD): %.2f\nETH Diff: %.2f" % (currentHashRate,reportedHashRate,activeWorkers,unpaid, usd_price*unpaid, pool_diff)
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)


    # Wallet Balance command
    def balance(self, update:Update, context: CallbackContext):
        eth_balance = self.get_current_balance()
        current_exchange_rate = self.get_exchange_rate()
        current_usd_balance = eth_balance * current_exchange_rate
        message = "ETH Balance: %.6f\nCurrent Exchange Rate (ETH/USD): %.2f\nCurrent USD Balance: %.6f" % (eth_balance, current_exchange_rate, current_usd_balance)
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)


    # Get data from ethermine dashboard
    def get_miner_info(self, target=None, function="dashboard"):
        if target is None:
            target = self.TARGET_WALLET
        uri = ETHERMINE_API_URI + "/miner/" + target + "/" + function
        data =  make_request(uri)
        currentHashRate = 0.0
        reportedHashRate = 0.0
        activeWorkers = 0.0
        unpaid = 0.0
        if data is None:
            pass
        else:
            jobj = json.loads(data)
            if jobj['status'] == "OK":
                status = jobj['data']['currentStatistics']
                currentHashRate = status['currentHashrate'] / 1e6
                reportedHashRate = status['reportedHashrate'] / 1e6
                activeWorkers = status['activeWorkers']
                unpaid = self.eth_conversion(float(status['unpaid']))
        return currentHashRate, reportedHashRate, activeWorkers, unpaid


    def eth_conversion(self, amount):
        if isinstance(amount,float):
            return amount / 1e18
        else:
            return None

    # Get pool difficulty (Deprecated)
    # def get_pool_status(self):
    #     uri = "https://eth.2miners.com/api/stats"
    #     header = {"accept": "application/json"}
    #     response = make_request(uri, header)
    #     data = json.loads(response)
    #     diff_rate = int(data["nodes"][0]["difficulty"]) / 1e15
    #     return diff_rate

    def get_pool_status(self):
        uri = "%s/%s" %(ETHERMINE_API_URI, "networkStats")
        response = make_request(uri)
        data = json.loads(response)
        if data["status"] == "OK":
            diff_rate = int(data["data"]["difficulty"]) / 1e15
            return diff_rate
        else:
            return 0


    # Get wallet balance from polygon network
    def get_current_balance(self, wallet=None, contract=None, token = None):
        if wallet is None:
            wallet = self.TARGET_WALLET
        if contract is None:
            contract = self.TARGET_CONTRACT
        if token is None:
            token = self.POLYGON_TOKEN
        uri = POLYGON_API_URI + "?module=account&action=tokenbalance&contractaddress=" + contract + "&address=0x" + wallet + "&apikey=" + token
        response = make_request(uri)
        data = json.loads(response)
        return self.eth_conversion(float(data['result']))


    # Get Exchange rate (ETH/USDT)
    def get_exchange_rate(self):
        #uri = "https://api.coinbase.com/v2/prices/ETH-USD/sell"
        uri = "%s/%s" %(ETHERMINE_API_URI, "poolStats")
        response = make_request(uri)
        data = json.loads(response)
        #return float(data['data']['amount'])
        if data["status"] == "OK":
            usd_price = float(data['data']['price']['usd'])
            return usd_price
        else:
            return 0



def main(argv):
    config_file = DEFAULT_CONFIG_FILE
    if len(argv) >= 2:
        args = parse_args(argv[1:]) # the first arg was the program name
        config_file = args.config_path
    my_bot = EthermineBot(config_file)
    my_bot.run()

if __name__ == "__main__":
    main(sys.argv)