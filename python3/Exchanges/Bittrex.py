import time
from datetime import datetime
import hmac
import hashlib
import requests
import pandas as pd

from Exchange import Exchange

class Bittrex(Exchange):
    def __init__(self, APIKey='', Secret=''):
        super().__init__(APIKey, Secret)
        """
            https://bittrex.github.io/api/v1-1
        """
        self._BASE_URL = 'https://bittrex.com/api/v1.1'
        self._tick_intervals = {
            'oneMin':       1,
            'fiveMin':      5,
            'thirtyMin':    30,
            'hour':         60,
            'day':          24*60
        }

    def get_request(self, url, base_url_override = None):
        if base_url_override is None:
            base_url_override = self._BASE_URL
        try:
            result = requests.get(base_url_override + url).json()
            if result.get('success', None) == True:
                self.log_request_success()
                return result['result']
            else:
                self.log_request_error(results['message'])
                if self.retry_count_not_exceeded():
                    return self.get_request(url, base_url_override)
                else:
                    return {}
        except Exception as e:
            self.log_request_error(base_url_override + url + ". " + str(e))
            if self.retry_count_not_exceeded():
                return self.get_request(url, base_url_override)
            else:
                return {}

    def trading_api_request(self, command, extra=''):
        try:
            nonce = str(int(time.time()*1000))
            request_url = self._BASE_URL + command + '?' + 'apikey=' + self._API_KEY + "&nonce=" + nonce + extra
            result = requests.get(
                request_url,
                headers={"apisign": hmac.new(self._API_SECRET.encode(), request_url.encode(), hashlib.sha512).hexdigest()}
            ).json()
            if result.get('success', None) == True:
                self.log_request_success()
                return result['result']
            else:
                self.log_request_error(result['message'])
                if self.retry_count_not_exceeded():
                    return self.trading_api_request(command, extra)
                else:
                    return {}

        except Exception as e:
            self.log_request_error(str(e))
            if self.retry_count_not_exceeded():
                return self.trading_api_request(command, extra)
            else:
                return {}

    ########################################
    ### Exchange specific public methods ###
    ########################################

    def get_currencies(self):
        """
            Used to get all supported currencies at Bittrex along with other
            meta data.
            Debug: ct['Bittrex'].get_currencies()
            [
                {
                  'BaseAddress': '1N52wHoVR79PMDishab2XmRHsbekCdGquK',
                  'CoinType': 'BITCOIN',
                  'Currency': 'BTC',
                  'CurrencyLong': 'Bitcoin',
                  'IsActive': True,
                  'IsRestricted': False,
                  'MinConfirmation': 2,
                  'Notice': None,
                  'TxFee': 0.0005
                },
                ...
              ]
        """
        return self.get_request('/public/getcurrencies')

    def get_markets(self):
        """
            Used to get the open and available trading markets at Bittrex along
            with other meta data
            Debug: ct['Bittrex'].get_markets()
            [
                {
                  'BaseCurrency': 'BTC',
                  'BaseCurrencyLong': 'Bitcoin',
                  'Created': '2014-02-13T00:00:00',
                  'IsActive': True,
                  'IsRestricted': False,
                  'IsSponsored': None,
                  'LogoUrl': 'https://bittrexblobstorage.blob.core.windows.net/public/6defbc41-582d-47a6-bb2e-d0fa88663524.png',
                  'MarketCurrency': 'LTC',
                  'MarketCurrencyLong': 'Litecoin',
                  'MarketName': 'BTC-LTC',
                  'MinTradeSize': 0.029886,
                  'Notice': None
                },
                ...
              ]
        """
        return self.get_request('/public/getmarkets')

    def get_ticker(self, market):
        """
            Used to get the current tick values for a market.
            Debug: ct['Bittrex'].get_ticker('BTC-LTC')
            {
              "Bid": 2.05670368,
              "Ask": 3.35579531,
              "Last": 3.35579531
            }
        """
        return self.get_request('/public/getticker?market=' + market)

    def get_market_summaries(self):
        """
            Used to get the last 24 hour summary of all active markets.
            Debug: ct['Bittrex'].get_market_summaries()
            [
                {
                  "Ask": 0.012911,
                  "BaseVolume": 47.03987026,
                  "Bid": 0.01271001,
                  "Created": "2014-02-13T00:00:00",
                  "High": 0.0135,
                  "Last": 0.01349998,
                  "Low": 0.012,
                  "MarketName": "BTC-LTC",
                  "OpenBuyOrders": 45,
                  "OpenSellOrders": 45,
                  "PrevDay": 0.01229501,
                  "TimeStamp": "2014-07-09T07:22:16.72",
                  "Volume": 3833.97619253
                }
              ]
        """
        return self.get_request('/public/getmarketsummaries')

    def get_market_summary(self, market):
        """
            Used to get the last 24 hour summary of a specific market.
            Debug: ct['Bittrex'].get_market_summary('BTC-LTC')
            [
                {
                  "Ask": 0.012911,
                  "BaseVolume": 47.03987026,
                  "Bid": 0.01271001,
                  "Created": "2014-02-13T00:00:00",
                  "High": 0.0135,
                  "Last": 0.01349998,
                  "Low": 0.012,
                  "MarketName": "BTC-LTC",
                  "OpenBuyOrders": 45,
                  "OpenSellOrders": 45,
                  "PrevDay": 0.01229501,
                  "TimeStamp": "2014-07-09T07:22:16.72",
                  "Volume": 3833.97619253
                }
              ]
        """
        return self.get_request('/public/getmarketsummary?market=' + market)

    def get_order_book(self, market, type = 'both'):
        """
            Used to get retrieve the orderbook for a given market.
            Debug: ct['Bittrex'].get_order_book('BTC-LTC')
            {
              "buy": [
                {
                  "Quantity": 12.37,
                  "Rate": 32.55412402
                },
                ...
              ],
              "sell": [
                {
                  "Quantity": 12.37,
                  "Rate": 32.55412402
                },
                ...
              ]
            }
        """
        return self.get_request('/public/getorderbook?market=' + market + '&type=' + type)

    def get_market_history(self, market):
        """
            Used to retrieve the latest trades that have occurred for a specific market.
            Debug: ct['Bittrex'].get_market_history('BTC-LTC')
            [
                {
                  "FillType": "FILL",
                  "Id": 319435,
                  "OrderType": "BUY",
                  "Price": 0.012634,
                  "Quantity": 0.30802438,
                  "TimeStamp": "2014-07-09T03:21:20.08",
                  "Total": 0.00389158,
                },
                ...
              ]
        """
        return self.get_request('/public/getmarkethistory?market=' + market)

    ########################################
    ### Exchange specific private methods ##
    ########################################

    def submit_buylimit(self, market, quantity, rate):
        """
            Used to place a buy order in a specific market. Use buylimit to
            place limit orders. Make sure you have the proper permissions set on
            your API keys for this call to work.
            Debug: ct['Bittrex'].submit_buylimit('BTC-CURE', 100, 0.00001405)
            {
                "uuid": "614c34e4-8d71-11e3-94b5-425861b86ab6"
              }
        """
        request = "&market={0}&quantity={1:.8f}&rate={2:.8f}".format(market, quantity, rate)
        return self.trading_api_request('/market/buylimit', request)

    def submit_selllimit(self, market, quantity, rate):
        """
            Used to place an sell order in a specific market. Use selllimit to
            place limit orders. Make sure you have the proper permissions set on
            your API keys for this call to work.
            Debug: ct['Bittrex'].submit_selllimit('BTC-LTC', 1.2, 1.3)
            {
                "uuid": "614c34e4-8d71-11e3-94b5-425861b86ab6"
              }
        """
        return self.trading_api_request('/market/buylimit', "&market={0}&quantity={1:.8f}&rate={2:.8f}".format(market, quantity, rate))

    def cancel_order(self, order_uuid):
        return self.trading_api_request('/market/cancel','&uuid='+order_uuid)

    def get_open_orders_in_market(self, market):
        """
            Get all orders that you currently have opened for a specific market.
            Debug: ct['Bittrex'].get_open_orders_in_market('BTC-LTC')
            [
                {
                  "CancelInitiated": "boolean",
                  "Closed": None,
                  "CommissionPaid": 0,
                  "Condition": 'NONE',
                  "ConditionTarget": None,
                  "Exchange": "BTC-LTC",
                  "ImmediateOrCancel": False,
                  "IsConditional": False,
                  "Limit": 1e-8,
                  "Opened": "2014-07-09T03:55:48.583",
                  "OrderType": "LIMIT_BUY",
                  "OrderUuid": "8925d746-bc9f-4684-b1aa-e507467aaa99",
                  "Price": 0,
                  "PricePerUnit": null,
                  "Quantity": 100000,
                  "QuantityRemaining": 100000,
                  "Uuid": None
                }
              ]
        """
        if self._API_KEY == '':
            return []
        else:
            return self.trading_api_request('/market/getopenorders','&market='+market)

    def get_all_open_orders(self):
        """
            Get all orders that you currently have opened in all markets.
            Debug: ct['Bittrex'].get_all_open_orders()
            [
                {
                  "CancelInitiated": "boolean",
                  "Closed": None,
                  "CommissionPaid": 0,
                  "Condition": 'NONE',
                  "ConditionTarget": None,
                  "Exchange": "BTC-LTC",
                  "ImmediateOrCancel": False,
                  "IsConditional": False,
                  "Limit": 1e-8,
                  "Opened": "2014-07-09T03:55:48.583",
                  "OrderType": "LIMIT_BUY",
                  "OrderUuid": "8925d746-bc9f-4684-b1aa-e507467aaa99",
                  "Price": 0,
                  "PricePerUnit": null,
                  "Quantity": 100000,
                  "QuantityRemaining": 100000,
                  "Uuid": None
                }
              ]
        """
        return self.trading_api_request('/market/getopenorders')

    def get_balances(self):
        """
            Used to retrieve all balances from your account.
            Debug: ct['Bittrex'].get_balances()
            [
                {
                  "Available": 4.21549076,
                  "Balance": 4.21549076,
                  "CryptoAddress": "DLxcEt3AatMyr2NTatzjsfHNoB9NT62HiF",
                  "Currency": "DOGE",
                  "Pending": 0
                }
              ]
        """
        return self.trading_api_request('/account/getbalances')

    def get_balance(self, currency):
        """
            Used to retrieve the balance from your account for a specific
            currency.
            Debug: ct['Bittrex'].get_balance('BTC')
            [
                {
                  "Available": 4.21549076,
                  "Balance": 4.21549076,
                  "CryptoAddress": "DLxcEt3AatMyr2NTatzjsfHNoB9NT62HiF",
                  "Currency": "DOGE",
                  "Pending": 0
                }
              ]
        """
        return self.trading_api_request('/account/getbalance', '&currency='+currency)

    def get_deposit_address(self, currency):
        """
            Used to retrieve or generate an address for a specific currency. If
            one does not exist, the call will fail and return ADDRESS_GENERATING
            until one is available.
            Debug: ct['Bittrex'].get_deposit_address('BTC')
            [
                {
                  "Address": "Vy5SKeKGXUHKS2WVpJ76HYuKAu3URastUo",
                  "Currency": "VTC",
                }
              ]
        """
        return self.trading_api_request('/account/getdepositaddress', '&currency='+currency)

    def withdraw(self, currency, quantity, address, paymentid = None):
        """
            Used to withdraw funds from your account. Note: please account for
            txfee.
            paymentid: string used for CryptoNotes/BitShareX/Nxt/XRP and any
            other coin that has a memo/message/tag/paymentid option
            Debug: ct['Bittrex'].withdraw('VTC', 1000, 'Vy5SKeKGXUHKS2WVpJ76HYuKAu3URastUo')
            {
                "uuid": "614c34e4-8d71-11e3-94b5-425861b86ab6"
              }
        """
        request = '&currency={0}&quantity={1:.8f}&address={2}'.format(currency, quantity, address)
        if paymentid is not None:
            request += '&paymentid='+paymentid
        return self.trading_api_request('/account/withdraw', request)

    def get_order(self, orderId):
        """
            Used to retrieve a single order by uuid
            Debug: ct['Bittrex'].get_order('0cb4c4e4-bdc7-4e13-8c13-430e587d2cc1')
            [
                {
                  "Uuid": "string (uuid)",
                  "OrderUuid": "8925d746-bc9f-4684-b1aa-e507467aaa99",
                  "Exchange": "BTC-LTC",
                  "OrderType": "string",
                  "Quantity": 100000,
                  "QuantityRemaining": 100000,
                  "Limit": 1e-8,
                  "CommissionPaid": 0,
                  "Price": 0,
                  "PricePerUnit": null,
                  "Opened": "2014-07-09T03:55:48.583",
                  "Closed": null,
                  "CancelInitiated": "boolean",
                  "ImmediateOrCancel": "boolean",
                  "IsConditional": "boolean"
                }
              ]
        """
        return self.trading_api_request('/account/getorder', '&uuid='+orderId)

    def get_order_history(self, market = None):
        """
            Used to retrieve a single order by uuid
            market: a string literal for the market (ie. BTC-LTC). If omitted,
            will return for all markets
            Debug: ct['Bittrex'].get_order_history()
            [
                {
                  "Closed": "2014-07-09T03:55:48.583",
                  "Commission": 0.00004921,
                  "Condition": 'NONE',
                  "ConditionTarget": None,
                  "Exchange": "BTC-LTC",
                  "ImmediateOrCancel": False,
                  "IsConditional": False,
                  "Limit": 1e-8,
                  "OrderType": "LIMIT_BUY",
                  "OrderUuid": "fd97d393-e9b9-4dd1-9dbf-f288fc72a185",
                  "Price": 0.01968424,
                  "PricePerUnit": 0.0000295,
                  "Quantity": 667.03644955,
                  "QuantityRemaining": 0,
                  "TimeStamp": "2014-07-09T03:55:48.583"
                }
              ]
        """
        request = ''
        if market is not None:
            request += '&market='+market
        return self.trading_api_request('/account/getorderhistory', request)

    def get_withdrawal_history(self, currency = None):
        """
            Used to retrieve your withdrawal history.
            currency: a string literal for the currency (ie. BTC). If omitted,
            will return for all currencies
            Debug: ct['Bittrex'].get_withdrawal_history()
            [
                {
                  "PaymentUuid": "b52c7a5c-90c6-4c6e-835c-e16df12708b1",
                  "Currency": "BTC",
                  "Amount": 17,
                  "Address": "1DeaaFBdbB5nrHj87x3NHS4onvw1GPNyAu",
                  "Opened": "2014-07-09T04:24:47.217",
                  "Authorized": "boolean",
                  "PendingPayment": "boolean",
                  "TxCost": 0.0002,
                  "TxId": "b4a575c2a71c7e56d02ab8e26bb1ef0a2f6cf2094f6ca2116476a569c1e84f6e",
                  "Canceled": "boolean",
                  "InvalidAddress": "boolean"
                }
              ]
        """
        request = ''
        if currency is not None:
            request += '&currency='+currency
        return self.trading_api_request('/account/getwithdrawalhistory', request)

    def get_deposit_history(self, currency = None):
        """
            Used to retrieve your deposit history.
            currency: a string literal for the currency (ie. BTC). If omitted,
            will return for all currencies
            Debug: ct['Bittrex'].get_deposit_history()
            [
                {
                  "Id": 1,
                  "Amount": 2.12345678,
                  "Currency": "BTC",
                  "Confirmations": 2,
                  "LastUpdated": "2014-02-13T07:38:53.883",
                  "TxId": "e26d3b33fcfc2cb0c74d0938034956ea590339170bf4102f080eab4b85da9bde",
                  "CryptoAddress": "15VyEAT4uf7ycrNWZVb1eGMzrs21BH95Va"
                }
              ]
        """
        request = ''
        if currency is not None:
            request += '&currency='+currency
        return self.trading_api_request('/account/getdeposithistory', request)

    #################################
    ### Additional custom methods ###
    #################################

    def get_balances_in_btc(self):
        balances = self.get_balances()['result']
        markets = self.get_market_summaries()['result']
        result = 0
        for balance in range(len(balances)):
            currency = balances[balance]['Currency']
            if currency == 'BTC':
                btc_rate = 1
            else:
                for market in range(len(markets)):
                    if markets[market]['MarketName'] == 'BTC-' + currency:
                        btc_rate = (markets[market]['Bid'] + markets[market]['Ask']) / 2
            result = result + balances[balance]['Balance'] * btc_rate
        return result

    def get_ticks(self, market, interval = 'fiveMin'):
        return self.get_request('https://bittrex.com/Api/v2.0/pub/market/GetTicks?marketName=' + market + '&tickInterval=' + interval, '')

    def get_latest_tick(self, market, interval = 'fiveMin'):
        return self.get_request('https://bittrex.com/Api/v2.0/pub/market/GetLatestTick?marketName=' + market + '&tickInterval=' + interval, '')

    def parse_timestamp(self, timestamp):
        millis = timestamp.find('.')
        if millis > 0:
            timestamp = timestamp[:millis]
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")

    #######################
    ### Generic methods ###
    #######################
    def get_formatted_currencies(self):
        """
            Loading currencies
            Debug: ct['Bittrex'].get_formatted_currencies()
            Example:
                {
                    'BTC': {
                                'Name': 'Bitcoin',
                                'DepositEnabled': True,
                                'WithdrawalEnabled': True,
                                'Notice': '',
                                'ExchangeBaseAddress': 'address',
                                'MinConfirmation': 2,
                                'WithdrawalFee': 0.001,
                                'WithdrawalMinAmount': 0.001,
                                'Precision': 0.00000001
                            },
                    ...
                }
        """
        currencies = self.get_currencies()
        results = {}
        if isinstance(currencies, list):
            for currency in currencies:
                try:
                    enabled = currency['IsActive'] and not currency['IsRestricted']
                    if currency.get('Notice', '') is None:
                        notice = ''
                    else:
                        notice = currency.get('Notice', '')
                    if currency.get('BaseAddress', '') is None:
                        address = ''
                    else:
                        address = currency.get('BaseAddress', '')
                    results[currency['Currency']] = {
                        'Name': currency['CurrencyLong'],
                        'DepositEnabled': enabled,
                        'WithdrawalEnabled': enabled,
                        'Notice': notice,
                        'ExchangeBaseAddress': address,
                        'MinConfirmation': currency.get('MinConfirmation', 0),
                        'WithdrawalFee': currency.get('TxFee', 0),
                        'WithdrawalMinAmount': 0,
                        'Precision': 0.00000001
                    }
                except Exception as e:
                    self.log_request_error(str(e))

        return results

    def update_market_definitions(self):
        """
            Used to get the open and available trading markets at Bittrex along
            with other meta data.
            * Assumes that currency mappings are already available
            Debug: ct['Bittrex'].update_market_definitions()
        """
        markets = self.get_markets()
        if isinstance(markets, list):
            for market in markets:
                try:
                    is_active = market.get('IsActive', None)
                    if is_active is None:
                        is_active = False
                    is_restricted = market.get('IsRestricted', None)
                    if is_restricted is None:
                        is_restricted = False
                    notice = market.get('Notice', '')
                    if notice is None:
                        notice = ''
                    self.update_market(
                        market['MarketName'],
                        {
                            'LocalBase':        market['BaseCurrency'],
                            'LocalCurr':        market['MarketCurrency'],
                            'BaseMinAmount':    0,
                            'BaseIncrement':    0.00000001,
                            'CurrMinAmount':    market.get('MinTradeSize', 0),
                            'CurrIncrement':    0.00000001,
                            'PriceMin':         0,
                            'PriceIncrement':   0.00000001,
                            'IsActive':         is_active,
                            'IsRestricted':     is_restricted,
                            'Notice':           notice,
                            'Created':          self.parse_timestamp(market['Created']),
                            'LogoUrl':          market['LogoUrl'],
                        }
                    )
                except Exception as e:
                    self.log_request_error(str(market) + ". " + str(e))

    def update_market_quotes(self):
        """
            Used to get best bids and asks across markets at Bittrex
            Debug: ct['Bittrex'].update_market_quotes()
        """
        market_summaries = self.get_market_summaries()
        if isinstance(market_summaries, list):
            for market in market_summaries:
                market_symbol = market['MarketName']
                try:
                    if market['PrevDay'] > 0:
                        percent_move = 100 * ((market['Bid'] + market['Ask']) / (2 * market['PrevDay']) - 1)
                    else:
                        percent_move = 0
                    self.update_market(
                        market_symbol,
                        {
                            'BaseVolume':       market['BaseVolume'],
                            'CurrVolume':       market['Volume'],
                            'BestBid':          market['Bid'],
                            'BestAsk':          market['Ask'],
                            '24HrHigh':         market['High'],
                            '24HrLow':          market['Low'],
                            '24HrPercentMove':  percent_move,
                            'LastTradedPrice':  market['Last'],
                            'TimeStamp':        self.parse_timestamp(market['TimeStamp']),
                        }
                    )
                except Exception as e:
                    self.log_request_error(str(market) + ". " + str(e))

    def update_market_24hrs(self):
        self.update_market_quotes()

    def update_user_open_orders_per_market(self, market):
        """
            Used to update outstanding orders
            Debug: ct['Bittrex'].update_user_market_open_orders('BTC-LTC')
        """
        open_orders = self.get_open_orders_in_market(market)
        results = []
        for order in open_orders:
            if order['OrderType'] == 'LIMIT_BUY':
                order_type = 'Buy'
            else:
                order_type = 'Sell'

            results.append({
                'OrderId': order['OrderUuid'],
                'OrderType': order_type,
                'OpderOpenedAt': self.parse_timestamp(order['Opened']),
                'Price': order.get('Limit',0),
                'Amount': order.get('Quantity',0),
                'Total': order.get('Price',0),
                'AmountRemaining': order.get('QuantityRemaining',0),
            })

        self._open_orders[market] = results

    def update_recent_market_trades_per_market(self, market):
        """
            Used to update recent market trades at a given market
            Debug: ct['Bittrex'].update_recent_market_trades_per_market('BTC-LTC')
        """
        trades = self.get_market_history(market)
        results = []
        for trade in trades:
            if trade['OrderType'] == 'BUY':
                order_type = 'Buy'
            else:
                order_type = 'Sell'

            if trade.get('Price',0) > 0 and trade.get('Quantity',0) > 0:
                results.append({
                    'TradeId': trade['Id'],
                    'TradeType': order_type,
                    'TradeTime': self.parse_timestamp(trade['TimeStamp']),
                    'Price': trade['Price'],
                    'Amount': trade['Quantity'],
                    'Total': trade['Total']
                })

        self._recent_market_trades[market] = results



    def load_markets(self):
        self._markets = {}
        self._active_markets = {}
        all_markets = self.get_market_summaries()

        for entry in all_markets:
            try:
                market_symbol = entry['MarketName']
                local_base = market_symbol[0:market_symbol.find('-')]
                local_curr = market_symbol[market_symbol.find('-')+1:]

                self.update_market(market_symbol, local_base, local_curr, entry['Bid'], entry['Ask'], True)
            except Exception as e:
                self.log_request_error(str(entry) + ". " + str(e))
        return self._active_markets

    def load_ticks(self, market_symbol, interval = 'fiveMin', lookback = None):
        load_chart = self.get_ticks(market_symbol, interval)
        results = []
        for i in load_chart:
            new_row = datetime.strptime(i['T'], "%Y-%m-%dT%H:%M:%S").timestamp(), i['O'], i['H'], i['L'], i['C'], i['V'], i['BV']
            results.append(new_row)
        return results

    def load_available_balances(self):
        available_balances = self.get_balances()
        self._available_balances = {}
        for balance in available_balances:
            currency = balance['Currency']
            self._available_balances[currency] = balance["Available"]
        return self._available_balances

    def load_balances_btc(self):
        balances = self.get_balances()
        self._complete_balances_btc = {}
        for balance in balances:
            try:
                currency = balance['Currency']
                available_balance = 0 if balance.get('Available',0) is None else balance.get('Available',0)
                total_balance = 0 if balance.get('Balance',0) is None else balance.get('Balance',0)
                self._complete_balances_btc[currency] = {
                    'Available': available_balance,
                    'OnOrders': total_balance - available_balance,
                    'Total': total_balance
                }
            except Exception as e:
                self.log_request_error(str(e))
        return self._complete_balances_btc

    def load_order_book(self, market, depth = 5):
        raw_results = self.get_order_book(market,'both')
        take_bid = min(depth, len(raw_results['buy']))
        take_ask = min(depth, len(raw_results['sell']))

        if take_bid == 0 and take_ask == 0:
            results = { 'Tradeable': 0, 'Bid': {}, 'Ask': {} }
        else:
            results = { 'Tradeable': 1, 'Bid': {}, 'Ask': {} }
        for i in range(take_bid):
            results['Bid'][i] = {
                'Price': raw_results['buy'][i]['Rate'],
                'Quantity': raw_results['buy'][i]['Quantity'],
            }
        for i in range(take_ask):
            results['Ask'][i] = {
                'Price': raw_results['sell'][i]['Rate'],
                'Quantity': raw_results['sell'][i]['Quantity'],
            }

        return results

    def submit_trade(self, direction, market, price, amount, trade_type):
        request = '&market=' + market + "&quantity={0:.8f}&rate={1:.8f}".format(amount, price)
        order_kind = '/market/buylimit'
        if direction == 'sell':
            order_kind = '/market/selllimit'
        trade = self.trading_api_request(order_kind,request)
        amount_traded = amount

        if trade_type == 'ImmediateOrCancel':
            time.sleep(.5)
            open_orders = self.get_open_orders_in_market(market)
            for open_order in open_orders:
                if open_order['OrderUuid'] == trade['uuid']:
                    self.cancel_order(trade['uuid'])
                    amount_traded = open_order['Quantity'] - open_order['QuantityRemaining']

        return {
                'Amount': amount_traded,
                'OrderNumber': trade['uuid']
            }
