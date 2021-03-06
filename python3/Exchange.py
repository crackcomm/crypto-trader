# Abstract Exchange class. Each exchange implementation should inherit from it.
import time
import traceback


class Exchange:
    def __init__(self, APIKey='', Secret='', PassPhrase=''):
        self.update_api_keys(APIKey, Secret, PassPhrase)
        self._BASE_URL = ''
        self._API_KEY = ''
        self._API_SECRET = ''
        self._API_PASSPHRASE = ''

        self._implements = {}

        self._currencies = {}
        self._markets = {}
        self._active_markets = {}
        self._balances = {}
        self._timestamps = {}

        self._map_currency_code_to_exchange_code = {}
        self._map_exchange_code_to_currency_code = {}
        self._map_market_to_global_codes = {}

        self._open_orders = {}
        self._recent_market_trades = {}
        self._recent_user_trades = {}

        self._order_book = {}

        self._market_prices = {}
        self._available_balances = {}
        self._complete_balances_btc = {}
        self._tick_intervals = {}
        self._tick_lookbacks = {}
        self._map_tick_intervals = {}
        self._max_error_count = 3
        self._error = {
            'count': 0,
            'message': '',
            'result_timestamp': time.time()
        }

    def update_api_keys(self, APIKey='', Secret='', PassPhrase=''):
        self._API_KEY = APIKey
        self._API_SECRET = Secret
        self._API_PASSPHRASE = PassPhrase

    def has_api_keys(self):
        return self._API_KEY != ''

    def has_implementation(self, name):
        return name in self._implements

    # ##### Error handling #####
    def raise_not_implemented_error(self):
        raise NotImplementedError("Class {} needs to implement method {}!!!".format(
                self.__class__.__name__,
                traceback.extract_stack(None, 2)[0][2]
            )
        )

    def log_request_success(self):
        self._error = {
            'count': 0,
            'message': '',
            'result_timestamp': time.time()
        }

    def log_request_error(self, message):
        error_message = 'Exception in class {} method {}: {}'.format(
            self.__class__.__name__,
            traceback.extract_stack(None, 2)[0][2],
            message
        )
        print(error_message)
        self._error = {
            'count': self._error['count'] + 1,
            'message': error_message
        }

    def retry_count_not_exceeded(self):
        return self._error['count'] < self._max_error_count

    # ##### Generic methods #####
    def get_consolidated_currency_definitions(self):
        """
            Returns currency definitions as a dictionary
        """
        self.raise_not_implemented_error()

    def update_currency_definitions(self):
        """
            get_consolidated_currency_definitions() needs to return a dictionary:
            exchange currency code to a dictionary
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
        currencies = self.get_consolidated_currency_definitions()
        for currency in currencies.keys():
            if currency in self._currencies:
                self._currencies[currency].update(currencies[currency])
            else:
                self._currencies[currency] = currencies[currency]
        self._timestamps['update_currency_definitions'] = time.time()

    def update_market_definitions(self):
        """
            Updates _markets with current market definitions
        """
        self.raise_not_implemented_error()

    def get_global_code(self, local_code):
        return self._map_exchange_code_to_currency_code.get(local_code, None)

    def get_local_code(self, global_code):
        return self._map_currency_code_to_exchange_code.get(global_code, None)

    def update_market(self, market_symbol, input_dict):
        """
            Updates self._markets and self._active_markets using provided
            market_symbol (exchange symbol for traded pair, e.g. 'BTC-ETH')
            local_base (exchange code for base currency)
            local_curr (exchange code for traded currency)
            update_dict contains a dictionary of data to update for the market:
            {
                'BaseMinAmount': 0,
                'BaseIncrement': 0.00000001,
                'CurrMinAmount': 0,
                'CurrIncrement': 0.00000001,
                'IsActive':      True,
                'IsRestricted':  False,
                'Notice':        '',
                'Created':       datetime,
                'LogoUrl':       'url',
            }
        """
        local_base = input_dict.pop('LocalBase', None)
        local_curr = input_dict.pop('LocalCurr', None)
        if local_base is not None and local_curr is not None:
            code_base = self.get_global_code(local_base)
            code_curr = self.get_global_code(local_curr)
            self._map_market_to_global_codes[market_symbol] = {
                'LocalBase': local_base,
                'LocalCurr': local_curr,
                'GlobalBase': code_base,
                'GlobalCurr': code_curr
            }
        else:
            if market_symbol in self._map_market_to_global_codes:
                code_base = self._map_market_to_global_codes[market_symbol]['GlobalBase']
                code_curr = self._map_market_to_global_codes[market_symbol]['GlobalCurr']
            else:
                code_base = self.get_global_code(local_base)
                code_curr = self.get_global_code(local_curr)

        if code_base not in self._markets:
            self._markets[code_base] = {}
        if code_curr not in self._markets[code_base]:
            self._markets[code_base][code_curr] = {}
        if code_base not in self._active_markets:
            self._active_markets[code_base] = {}
        if code_curr not in self._active_markets[code_base]:
            self._active_markets[code_base][code_curr] = {}

        update_dict = {
            'MarketSymbol':     market_symbol,
            'BaseMinAmount':    0,
            'BaseIncrement':    0.00000001,
            'CurrMinAmount':    0,
            'CurrIncrement':    0.00000001,
            'PriceMin':         0,
            'PriceIncrement':   0.00000001,
            'IsActive':         True,
            'IsRestricted':     False,
            'Notice':           '',
        }
        update_dict.update(input_dict)
        self._markets[code_base][code_curr].update(update_dict)

        if update_dict['IsActive'] and not update_dict['IsRestricted']:
            self._active_markets[code_base][code_curr].update(update_dict)
        else:
            self._active_markets[code_base].pop(code_curr)

    def get_market_symbol(self, code_base, code_curr):
        return self._markets[code_base][code_curr]['MarketSymbol']

    def update_market_quotes(self):
        """
            Updates _markets with current market definitions
        """
        self.raise_not_implemented_error()

    def update_market_24hrs(self):
        """
            Updates _markets with current market definitions
        """
        self.raise_not_implemented_error()

    def update_open_user_orders_in_market(self, market):
        """
            get_consolidated_open_user_orders_in_market() needs to return a list
            Example:
            [
                {
                    'OrderId': exchangeOrderId,
                    'OrderType': order_type, # Buy / Sell
                    'OrderOpenedAt': datetime.datetime,
                    'Price': double,
                    'Amount': double,
                    'Total': double,
                    'AmountRemaining': double
                },
                ...
            ]
        """
        self._open_orders[market] = self.get_consolidated_open_user_orders_in_market(market)
        self._timestamps['update_open_user_orders_in_market'] = time.time()

    def update_recent_market_trades_per_market(self, market):
        """
            get_consolidated_recent_market_trades_per_market() needs to return a list
            Example:
            [
                {
                    'TradeId': string,
                    'TradeType': order_type,  # Buy / Sell
                    'TradeTime': datetime.datetime,
                    'Price': double,
                    'Amount': double,
                    'Total': double
                },
                ...
            ]
        """
        self._recent_market_trades[market] = self.get_consolidated_recent_market_trades_per_market(market)
        self._timestamps['update_recent_market_trades_per_market'] = time.time()

    def load_available_balances(self):
        """
            Returns a map by currency code and exchange showing available balances
        """
        self.raise_not_implemented_error()

    def load_balances_btc(self):
        """
            Returns a map by currency code and exchange showing available balances in currency terms and in btc terms
        """
        self.raise_not_implemented_error()

    def get_consolidated_order_book(self, market, depth):
        """
            Returns a short order book around best quotes in the following format:
            {'Ask': {0: {'Price': 0.00876449, 'Quantity': 13.0407078},
                     1: {'Price': 0.00876901, 'Quantity': 1.78},
                     2: {'Price': 0.00878253, 'Quantity': 0.91},
                     3: {'Price': 0.00878498, 'Quantity': 34.36},
                     4: {'Price': 0.00879498, 'Quantity': 5.36827355}},
             'Bid': {0: {'Price': 0.00874998, 'Quantity': 0.06902944},
                     1: {'Price': 0.00874598, 'Quantity': 12.62079594},
                     2: {'Price': 0.00874049, 'Quantity': 0.77},
                     3: {'Price': 0.0087315, 'Quantity': 0.46},
                     4: {'Price': 0.00872501, 'Quantity': 72.15}},
             'Tradeable': 1}
        """
        self.raise_not_implemented_error()

    def get_consolidated_klines(self, market_symbol, interval, lookback):
        """
            interval is an exchange specific name, e.g. 'fiveMin'
            Returns a candlestick data: times, opens, closes, ...
            Example:
            [
                (
                    time, - timestamp in seconds
                    open,
                    high,
                    low,
                    close,
                    volume,
                    baseVolume
                )
            ]
        """
        self.raise_not_implemented_error()

    def load_chart_data(self, market_symbol, interval, lookback):
        """
            interval and lookback come in terms of number of minutes
        """
        self._map_tick_intervals = {}
        take_i_name = None
        take_i_mins = None
        for i_name in self._tick_intervals:
            i_mins = self._tick_intervals[i_name]
            self._map_tick_intervals[i_mins] = i_name
            if take_i_mins is None or (interval >= i_mins > take_i_mins):
                take_i_mins = i_mins
                take_i_name = i_name

        preliminary_ticks = self.get_consolidated_klines(market_symbol, take_i_name, lookback)
        if preliminary_ticks is not None:
            if take_i_mins == interval:
                results = []
                for entry in preliminary_ticks:
                    if entry[0] >= preliminary_ticks[-1][0] - lookback * 60:
                        results.append(entry)
                return results
            else:
                results = []
                result_dict = {}
                for entry in preliminary_ticks:
                    agg_timestamp = int(entry[0] - entry[0] % (interval * 60))
                    if agg_timestamp in result_dict:
                        result_dict[agg_timestamp]['h'] = max(result_dict[agg_timestamp]['h'], entry[2])
                        result_dict[agg_timestamp]['l'] = min(result_dict[agg_timestamp]['l'], entry[3])
                        result_dict[agg_timestamp]['c'] = entry[4]
                        result_dict[agg_timestamp]['v'] += entry[5]
                        result_dict[agg_timestamp]['bv'] += entry[6]
                    else:
                        result_dict[agg_timestamp] = {
                            'o': entry[1],
                            'h': entry[2],
                            'l': entry[3],
                            'c': entry[4],
                            'v': entry[5],
                            'bv': entry[6]
                        }

                for agg_timestamp in result_dict:
                    if agg_timestamp >= preliminary_ticks[-1][0] - lookback * 60:
                        new_row = (agg_timestamp,
                                   result_dict[agg_timestamp]['o'],
                                   result_dict[agg_timestamp]['h'],
                                   result_dict[agg_timestamp]['l'],
                                   result_dict[agg_timestamp]['c'],
                                   result_dict[agg_timestamp]['v'],
                                   result_dict[agg_timestamp]['bv'])
                        results.append(new_row)

                return results

    def submit_trade(self, direction="buy", market="", price=0, amount=0, trade_type=""):
        """
            Submits a trade with specified parameters. Returns json with amount traded.
            Example:

        """
        self.raise_not_implemented_error()

    @staticmethod
    def order_params_for_sig(data):
        """Convert params to ordered string for signature

        :param data:
        :return: ordered parameters like amount=10&price=1.1&type=BUY

        """
        string_list = []
        for key in sorted(data):
            string_list.append("{}={}".format(key, data[key]))
        return '&'.join(string_list)

    def get_available_balance(self, currency, force_update=False):
        if not self._available_balances or force_update:
            self.load_available_balances()
        return self._available_balances.get(currency, 0)
