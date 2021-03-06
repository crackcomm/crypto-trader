import hashlib
import hmac
import json
import time
from datetime import datetime

import requests
import websocket
from PyQt5.QtCore import QThreadPool

from Exchange import Exchange
from Worker import CTWorker


class Binance(Exchange):
    def __init__(self, APIKey='', Secret=''):
        super().__init__(APIKey, Secret)
        """
            https://github.com/binance-exchange/binance-official-api-docs
            https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md
            https://github.com/binance-exchange/binance-official-api-docs/blob/master/web-socket-streams.md
        """
        self._BASE_URL = 'https://api.binance.com'
        self._exchangeInfo = None
        self._tick_intervals = {
            '1m':   1,
            '3m':   3,
            '5m':   5,
            '15m':  15,
            '30m':  30,
            '1h':   60,
            '2h':   2*60,
            '4h':   4*60,
            '6h':   6*60,
            '8h':   8*60,
            '12h':  12*60,
            '1d':   24*60,
            '3d':   3*24*60,
            '1w':   7*24*60,
            '1M':   30*24*60
        }
        self._timestamp_correction = int(self.public_get_server_time()) - int(time.time()*1000)
        self.public_update_exchange_info()
        self._thread_pool = QThreadPool()
        self._thread_pool.start(CTWorker(self.ws_init))

        self._ws = None
        self._implements = {
            'ws_24hour_market_moves',
            'ws_all_markets_best_bid_ask',
        }

    def public_get_request(self, url):
        try:
            results = requests.get(self._BASE_URL + url).json()
            if 'code' in results:
                self.log_request_error(results['msg'])
                if self.retry_count_not_exceeded():
                    return self.public_get_request(url)
                else:
                    return {}
            else:
                self.log_request_success()
                return results
        except Exception as e:
            self.log_request_error(self._BASE_URL + url)
            if self.retry_count_not_exceeded():
                return self.public_get_request(url)
            else:
                return {}

    def private_request(self, method, url, req={}):
        try:
            req['timestamp'] = int(time.time()*1000) + self._timestamp_correction
            query_string = '&'.join(["{}={}".format(k, v) for k, v in req.items()])
            signature = hmac.new(self._API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
            query_string = query_string + '&signature=' + signature

            headers = {'X-MBX-APIKEY': self._API_KEY}

            req_url = self._BASE_URL + url + '?' + query_string
            results = getattr(requests, method)(req_url, headers=headers).json()
            if 'code' in results:
                self.log_request_error(results['msg'])
                if self.retry_count_not_exceeded():
                    return self.private_request(method, url, req)
                else:
                    return {}
            else:
                self.log_request_success()
                return results
        except Exception as e:
            self.log_request_error(str(e))
            if self.retry_count_not_exceeded():
                return self.private_request(method, url, req)
            else:
                return {}

    # ############################################
    # ##### Exchange specific public methods #####
    # ############################################

    def public_get_ping(self):
        """
            Test connectivity to the Rest API.
            Debug: ct['Binance'].public_get_ping()
            {}
        """
        return self.public_get_request('/api/v1/ping')

    def public_get_server_time(self):
        """
            Test connectivity to the Rest API and get the current server time.
            Debug: ct['Binance'].public_get_server_time()
            1500000000000
        """
        return self.public_get_request('/api/v1/time').get('serverTime', None)

    def public_update_exchange_info(self):
        """
            Current exchange trading rules and symbol information
            Debug: ct['Binance'].public_update_exchangeInfo()
            {'exchangeFilters': [],
             'rateLimits': [{'interval': 'MINUTE',
                             'intervalNum': 1,
                             'limit': 1200,
                             'rateLimitType': 'REQUEST_WEIGHT'},
                            {'interval': 'SECOND',
                             'intervalNum': 1,
                             'limit': 10,
                             'rateLimitType': 'ORDERS'},
                            {'interval': 'DAY',
                             'intervalNum': 1,
                             'limit': 100000,
                             'rateLimitType': 'ORDERS'}],
             'serverTime': 1500000000000,
             'symbols': [{'baseAsset': 'ETH',
                          'baseAssetPrecision': 8,
                          'filters': [{'filterType': 'PRICE_FILTER',
                                       'maxPrice': '0.00000000',
                                       'minPrice': '0.00000000',
                                       'tickSize': '0.00000100'},
                                      {'avgPriceMins': 5,
                                       'filterType': 'PERCENT_PRICE',
                                       'multiplierDown': '0.1',
                                       'multiplierUp': '10'},
                                      {'filterType': 'LOT_SIZE',
                                       'maxQty': '100000.00000000',
                                       'minQty': '0.00100000',
                                       'stepSize': '0.00100000'},
                                      {'applyToMarket': True,
                                       'avgPriceMins': 5,
                                       'filterType': 'MIN_NOTIONAL',
                                       'minNotional': '0.00100000'},
                                      {'filterType': 'ICEBERG_PARTS', 'limit': 10},
                                      {'filterType': 'MAX_NUM_ALGO_ORDERS',
                                       'maxNumAlgoOrders': 5}],
                          'icebergAllowed': True,
                          'orderTypes': ['LIMIT',
                                         'LIMIT_MAKER',
                                         'MARKET',
                                         'STOP_LOSS_LIMIT',
                                         'TAKE_PROFIT_LIMIT'],
                          'quoteAsset': 'BTC',
                          'quotePrecision': 8,
                          'status': 'TRADING',
                          'symbol': 'ETHBTC'},
                          ...
                         {'baseAsset': 'WAVES',
                          'baseAssetPrecision': 8,
                          'filters': [{'filterType': 'PRICE_FILTER',
                                       'maxPrice': '100000.00000000',
                                       'minPrice': '0.00010000',
                                       'tickSize': '0.00010000'},
                                      {'avgPriceMins': 5,
                                       'filterType': 'PERCENT_PRICE',
                                       'multiplierDown': '0.1',
                                       'multiplierUp': '10'},
                                      {'filterType': 'LOT_SIZE',
                                       'maxQty': '10000000.00000000',
                                       'minQty': '0.01000000',
                                       'stepSize': '0.01000000'},
                                      {'applyToMarket': True,
                                       'avgPriceMins': 5,
                                       'filterType': 'MIN_NOTIONAL',
                                       'minNotional': '10.00000000'},
                                      {'filterType': 'ICEBERG_PARTS', 'limit': 10},
                                      {'filterType': 'MAX_NUM_ALGO_ORDERS',
                                       'maxNumAlgoOrders': 5}],
                          'icebergAllowed': True,
                          'orderTypes': ['LIMIT',
                                         'LIMIT_MAKER',
                                         'MARKET',
                                         'STOP_LOSS_LIMIT',
                                         'TAKE_PROFIT_LIMIT'],
                          'quoteAsset': 'USDC',
                          'quotePrecision': 8,
                          'status': 'TRADING',
                          'symbol': 'WAVESUSDC'}],
             'timezone': 'UTC'}
        """
        self._exchangeInfo = self.public_get_request('/api/v1/exchangeInfo')
        return self._exchangeInfo

    def public_get_order_book(self, market, depth='5'):
        """
            Get order book for a given currency pair (market).
            Valid depth values: 5, 10, 20, 50, 100, 500, 1000
            Debug: ct['Binance'].public_get_order_book('ETHBTC')
            {'asks': [['0.03299700', '1.00000000', []],
                      ['0.03299800', '1.00000000', []],
                      ...
                      ['0.03300000', '1.00000000', []]],
             'bids': [['0.03299400', '1.00000000', []],
                      ['0.03299300', '1.00000000', []],
                      ...
                      ['0.03299000', '1.00000000', []]],
             'lastUpdateId': 400000000}
        """
        url = "/api/v1/depth?symbol={}&limit={}".format(market, depth)
        return self.public_get_request(url)

    def public_get_market_history(self, market, limit='500'):
        """
            Get recent trades.
            Debug: ct['Binance'].public_get_market_history('ETHBTC')
            [{'id': 400000000,
              'isBestMatch': True,
              'isBuyerMaker': True,
              'price': '0.03300000',
              'qty': '1.00000000',
              'time': 1500000000000},
              ...
              ]
        """
        url = "/api/v1/trades?symbol={}&limit={}".format(market, limit)
        return self.public_get_request(url)

    # def get_trade_history(self, market, limit = '500', fromId = None):
    #     """
    #         Get trade history.
    #         fromId: TradeId to fetch from. Default gets most recent trades.
    #         Debug: ct['Binance'].get_trade_history('ETHBTC')
    #         {"code":-2014,"msg":"API-key format invalid."}
    #     """
    #     if fromId is None:
    #         fromIdStr = ''
    #     else:
    #         fromIdStr = '&fromId={}'.format(fromId)
    #     url = "/api/v1/historicalTrades?symbol={}&limit={}{}".format(market, limit, fromIdStr)
    #     return self.public_get_request(url)

    def public_get_aggregated_trades(self, market, limit='500', start_id=None, start_time=None, end_time=None):
        """
            Get compressed, aggregate trades. Trades that fill at the time, from
            the same order, with the same price will have the quantity aggregated.
            fromId: ID to get aggregate trades from INCLUSIVE.
            startTime: Timestamp in ms to get aggregate trades from INCLUSIVE.
            endTime: Timestamp in ms to get aggregate trades until INCLUSIVE.
            If both startTime and endTime are sent, time between startTime and
            endTime must be less than 1 hour.
            If fromId, startTime, and endTime are not sent, the most recent
            aggregate trades will be returned.
            Debug: ct['Binance'].public_get_aggregated_trades('ETHBTC')
            [{'M': True,            // Was the trade the best price match?
              'T': 1500000000000,   // Timestamp
              'a': 90000000,        // Aggregate tradeId
              'f': 100000000,       // First tradeId
              'l': 100000000,       // Last tradeId
              'm': False,           // Was the buyer the maker?
              'p': '0.01000000',    // Price
              'q': '1.00000000'},   // Quantity
              ...
              ]
        """
        additional_string = ''
        if start_id is not None:
            additional_string += '&fromId={}'.format(start_id)
        if start_time is not None:
            additional_string += '&startTime={}'.format(start_time)
        if end_time is not None:
            additional_string += '&endTime={}'.format(end_time)
        url = "/api/v1/aggTrades?symbol={}&limit={}{}".format(market, limit, additional_string)
        return self.public_get_request(url)

    def public_get_candlesticks(self, market, interval='5m', limit=100, start_time=None, end_time=None):
        """
            Kline/candlestick bars for a symbol. Klines are uniquely identified
            by their open time.
            Debug: ct['Binance'].public_get_candlesticks('ETHBTC', '15m', 100)
            [[1499040000000,      // Open time
              "0.01634790",       // Open
              "0.80000000",       // High
              "0.01575800",       // Low
              "0.01577100",       // Close
              "148976.11427815",  // Volume
              1499644799999,      // Close time
              "2434.19055334",    // Quote asset volume
              308,                // Number of trades
              "1756.87402397",    // Taker buy base asset volume
              "28.46694368",      // Taker buy quote asset volume
              "17928899.62484339" // Ignore. ? :)
              ],
              ...
              ]
        """
        additional_string = ''
        if limit is not None:
            additional_string += '&limit={}'.format(limit)
        if start_time is not None:
            additional_string += '&startTime={}'.format(start_time)
        if end_time is not None:
            additional_string += '&endTime={}'.format(end_time)
        url = "/api/v1/klines?symbol={}&interval={}{}".format(market, interval, additional_string)
        return self.public_get_request(url)

    def public_get_avg_price(self, market):
        """
            Current average price for a symbol.
            Debug: ct['Binance'].public_get_avg_price('ETHBTC')
            {'mins': 5, 'price': '0.03300000'}
        """
        return self.public_get_request("/api/v3/avgPrice?symbol={}".format(market))

    def public_get_24hour_statistics(self, market=None):
        """
            24 hour rolling window price change statistics. Careful when
            accessing this with no symbol.
            Weight: 1 for a single symbol; 40 when the symbol parameter is
            omitted
            Debug: ct['Binance'].public_get_24hour_statistics('ETHBTC')
            {'askPrice': '0.03300000',
             'askQty': '1.00000000',
             'bidPrice': '0.03300000',
             'bidQty': '1.00000000',
             'closeTime': 1499040000000,
             'count': 150000,                   // Trade count
             'firstId': 103250000,              // First tradeId
             'highPrice': '0.03300000',
             'lastId': 103400000,               // Last tradeId
             'lastPrice': '0.03300000',
             'lastQty': '1.00000000',
             'lowPrice': '0.03300000',
             'openPrice': '0.03300000',
             'openTime': 1499040000000,
             'prevClosePrice': '0.03300000',
             'priceChange': '0.00000000',
             'priceChangePercent': '0.000',
             'quoteVolume': '1.00000000',
             'symbol': 'BNBBTC',
             'volume': '1.00000000',
             'weightedAvgPrice': '0.03300000'}
             or [{...},...,{...}] if no symbol provided
        """
        if market is None:
            additional_string = ''
        else:
            additional_string = '?symbol={}'.format(market)
        url = "/api/v1/ticker/24hr{}".format(additional_string)
        return self.public_get_request(url)

    def public_get_latest_prices(self, market=None):
        """
            Latest price for a symbol or symbols.
            Debug: ct['Binance'].public_get_latest_prices('ETHBTC')
            {'price': '0.03300000', 'symbol': 'ETHBTC'}
        """
        if market is None:
            additional_string = ''
        else:
            additional_string = '?symbol={}'.format(market)
        url = "/api/v3/ticker/price{}".format(additional_string)
        return self.public_get_request(url)

    def public_get_ticker(self, market=None):
        """
            Best price/qty on the order book for a symbol or symbols.
            Debug: ct['Binance'].public_get_ticker('ETHBTC')
            {'askPrice': '0.03310000',
             'askQty': '1.00000000',
             'bidPrice': '0.03300000',
             'bidQty': '1.00000000',
             'symbol': 'ETHBTC'}
        """
        if market is None:
            additional_string = ''
        else:
            additional_string = '?symbol={}'.format(market)
        url = "/api/v3/ticker/bookTicker{}".format(additional_string)
        return self.public_get_request(url)

    # #############################################
    # ##### Exchange specific private methods #####
    # #############################################

    def private_submit_trade(self, symbol, side, order_type, quantity, time_in_force='GTC', price=None,
                             new_client_order_id=None, stop_price=None, iceberg_quantity=None,
                             new_order_response_type='RESULT', receive_window=None):
        """
            Send in a new order.
            newClientOrderId: A unique id for the order. Automatically generated
                if not sent.
            stopPrice: Used with STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, and
                TAKE_PROFIT_LIMIT orders.
            icebergQty: Used with LIMIT, STOP_LOSS_LIMIT, and TAKE_PROFIT_LIMIT
                to create an iceberg order.
            newOrderRespType: Set the response JSON. ACK, RESULT, or FULL;
                MARKET and LIMIT order types default to FULL, all other orders
                default to ACK.
            Debug: ct['Binance'].private_submit_trade('INSBTC', 'BUY', 'LIMIT', 100, 'GTC', 0.0001)
            {'clientOrderId': 'BiNanCeG3N3RaT3DaLpHaNuMeRiC',
             'cummulativeQuoteQty': '0.00000000',
             'executedQty': '0.00000000',
             'orderId': 20000000,
             'origQty': '100.00000000',
             'price': '0.00010000',
             'side': 'BUY',
             'status': 'NEW',
             'symbol': 'INSBTC',
             'timeInForce': 'GTC',
             'transactTime': 1540000000000,
             'type': 'LIMIT'}
        """
        request = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': "{0:.8f}".format(quantity),
                'timeInForce': time_in_force,
                'newOrderRespType': new_order_response_type
            }
        if price is not None:
            request['price'] = "{0:.8f}".format(price)
        if new_client_order_id is not None:
            request['newClientOrderId'] = new_client_order_id
        if stop_price is not None:
            request['stopPrice'] = "{0:.8f}".format(stop_price)
        if iceberg_quantity is not None:
            request['icebergQty'] = "{0:.8f}".format(iceberg_quantity)
        if receive_window is not None:
            request['recvWindow'] = "{}".format(receive_window)
        return self.private_request('post', '/api/v3/order', request)

    def private_test_submit_new_order(self, symbol, side, order_type, quantity, time_in_force='GTC', price=None,
                                      new_client_order_id=None, stop_price=None, iceberg_quantity=None,
                                      new_order_response_type='RESULT', receive_window=None):
        """
            Test new order creation and signature/recvWindow long. Creates and
            validates a new order but does not send it into the matching engine.
            Parameters same as private_submit_new_order()
            Debug: ct['Binance'].private_test_submit_new_order('INSBTC', 'BUY', 'LIMIT', 100, 'GTC', 0.0001)
            {}
        """
        request = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': "{0:.8f}".format(quantity),
                'timeInForce': time_in_force,
                'newOrderRespType': new_order_response_type
            }
        if price is not None:
            request['price'] = "{0:.8f}".format(price)
        if new_client_order_id is not None:
            request['newClientOrderId'] = new_client_order_id
        if stop_price is not None:
            request['stopPrice'] = "{0:.8f}".format(stop_price)
        if iceberg_quantity is not None:
            request['icebergQty'] = "{0:.8f}".format(iceberg_quantity)
        if receive_window is not None:
            request['recvWindow'] = "{}".format(receive_window)
        return self.private_request('post', '/api/v3/order/test', request)

    def private_get_order_status(self, market, order_id=None, original_client_order_id=None, receive_window=None):
        """
            Check an order's status.
            Either orderId or origClientOrderId must be sent.
            Debug: ct['Binance'].private_get_order_status('INSBTC',None, 'XWvrCHRVgsWjwOCrm5Ddwd')
            {'clientOrderId': 'BiNanCeG3N3RaT3DaLpHaNuMeRiC',
             'cummulativeQuoteQty': '0.00000000',
             'executedQty': '0.00000000',
             'icebergQty': '0.00000000',
             'isWorking': True,
             'orderId': 20000000,
             'origQty': '100.00000000',
             'price': '0.00010000',
             'side': 'BUY',
             'status': 'NEW',
             'stopPrice': '0.00000000',
             'symbol': 'INSBTC',
             'time': 1540000000000,
             'timeInForce': 'GTC',
             'type': 'LIMIT',
             'updateTime': 1540000000000}
        """
        request = {
                'symbol': market
            }
        if order_id is not None:
            request['orderId'] = order_id
        if original_client_order_id is not None:
            request['origClientOrderId'] = original_client_order_id
        if receive_window is not None:
            request['recvWindow'] = receive_window
        return self.private_request('get', '/api/v3/order', request)

    def private_cancel_order(self, market, order_id=None, original_client_order_id=None, new_client_order_id=None,
                             receive_window=None):
        """
            Cancel an active order.
            Either orderId or origClientOrderId must be sent.
            Debug: ct['Binance'].private_cancel_order('INSBTC', None, 'XWvrCHRVgsWjwOCrm5Ddwd')
            {'clientOrderId': 'NeW_BiNanCeG3N3RaT3DaLpHaNuMeRiC',
             'cummulativeQuoteQty': '0.00000000',
             'executedQty': '0.00000000',
             'orderId': 20000000,
             'origClientOrderId': 'BiNanCeG3N3RaT3DaLpHaNuMeRiC',
             'origQty': '100.00000000',
             'price': '0.00010000',
             'side': 'BUY',
             'status': 'CANCELED',
             'symbol': 'INSBTC',
             'timeInForce': 'GTC',
             'type': 'LIMIT'}
        """
        request = {
                'symbol': market
            }
        if order_id is not None:
            request['orderId'] = order_id
        if original_client_order_id is not None:
            request['origClientOrderId'] = original_client_order_id
        if new_client_order_id is not None:
            request['newClientOrderId'] = new_client_order_id
        if receive_window is not None:
            request['recvWindow'] = receive_window
        return self.private_request('delete', '/api/v3/order', request)

    def private_get_open_orders(self, market=None, receive_window=None):
        """
            Get all open orders on a symbol. Careful when accessing this with no
            symbol. Weight: 1 for a single symbol; 40 when the symbol parameter
            is omitted.
            Debug: ct['Binance'].private_get_open_orders('INSBTC')
            [{'clientOrderId': 'BiNanCeG3N3RaT3DaLpHaNuMeRiC',
              'cummulativeQuoteQty': '0.00000000',
              'executedQty': '0.00000000',
              'icebergQty': '0.00000000',
              'isWorking': True,
              'orderId': 20000000,
              'origQty': '100.00000000',
              'price': '0.00010000',
              'side': 'BUY',
              'status': 'NEW',
              'stopPrice': '0.00000000',
              'symbol': 'INSBTC',
              'time': 1540000000000,
              'timeInForce': 'GTC',
              'type': 'LIMIT',
              'updateTime': 1540000000000},
             ...
             ]
        """
        if self.has_api_keys():
            request = {}
            if market is not None:
                request['symbol'] = market
            if receive_window is not None:
                request['recvWindow'] = receive_window
            return self.private_request('get', '/api/v3/openOrders', request)
        else:
            return []

    def private_get_all_orders(self, market, start_order_id=None, start_time=None, end_time=None, limit='500',
                               receive_window=None):
        """
            Get all account orders; active, canceled, or filled.
            Weight: 5 with symbol
            Debug: ct['Binance'].private_get_all_orders('INSBTC')
            [{'clientOrderId': 'BiNanCeG3N3RaT3DaLpHaNuMeRiC',
              'cummulativeQuoteQty': '0.00000000',
              'executedQty': '0.00000000',
              'icebergQty': '0.00000000',
              'isWorking': True,
              'orderId': 20000000,
              'origQty': '100.00000000',
              'price': '0.00010000',
              'side': 'BUY',
              'status': 'FILLED',
              'stopPrice': '0.00000000',
              'symbol': 'INSBTC',
              'time': 1540000000000,
              'timeInForce': 'GTC',
              'type': 'LIMIT',
              'updateTime': 1540000000000},
             ...
             ]
        """
        if self.has_api_keys():
            request = {
                    'symbol': market,
                    'limit': limit
                }
            if start_order_id is not None:
                request['orderId'] = start_order_id
            if start_time is not None:
                request['startTime'] = start_time
            if end_time is not None:
                request['endTime'] = end_time
            if receive_window is not None:
                request['recvWindow'] = receive_window
            return self.private_request('get', '/api/v3/allOrders', request)
        else:
            return []

    def private_get_account_info(self, receive_window=None):
        """
            Get current account information.
            Weight: 5
            Debug: ct['Binance'].private_get_account_info()
            {'balances': [{'asset': 'BTC', 'free': '0.00000000', 'locked': '0.00000000'},
                          {'asset': 'LTC', 'free': '0.00000000', 'locked': '0.00000000'},
                          ...
                          {'asset': 'BCHSV', 'free': '0.00000000', 'locked': '0.00000000'},
                          {'asset': 'REN', 'free': '0.00000000', 'locked': '0.00000000'}],
             'buyerCommission': 0,
             'canDeposit': True,
             'canTrade': True,
             'canWithdraw': True,
             'makerCommission': 10,
             'sellerCommission': 0,
             'takerCommission': 10,
             'updateTime': 1540000000000}
        """
        if self.has_api_keys():
            request = {}
            if receive_window is not None:
                request['recvWindow'] = receive_window
            return self.private_request('get', '/api/v3/account', request)
        else:
            return {}

    def private_get_account_trades(self, market, start_order_id=None, start_time=None, end_time=None, limit='500',
                                   receive_window=None):
        """
            Get trades for a specific account and symbol. If start_order_id is set, it
            will get orders >= that start_order_id. Otherwise most recent orders are
            returned.
            Weight: 5 with symbol

        """
        request = {
                'symbol': market,
                'limit': limit
            }
        if start_order_id is not None:
            request['orderId'] = start_order_id
        if start_time is not None:
            request['startTime'] = start_time
        if end_time is not None:
            request['endTime'] = end_time
        if receive_window is not None:
            request['recvWindow'] = receive_window
        return self.private_request('get', '/api/v3/myTrades', request)

    # def start_user_data_stream(self):
    #     """
    #         Start a new user data stream. The stream will close after 60 minutes
    #         unless a keepalive is sent.
    #         ct['Binance'].start_user_data_stream()
    #         {'code': -1101, 'msg': "Too many parameters; expected '0' and received '2'."}
    #     """
    #     return self.private_request('post', '/api/v1/userDataStream')
    #
    # def keepalive_user_data_stream(self, listenKey):
    #     """
    #         Keepalive a user data stream to prevent a time out. User data
    #         streams will close after 60 minutes. It's recommended to send a ping
    #         about every 30 minutes.
    #     """
    #     request = {
    #             'listenKey': listenKey
    #         }
    #     return self.private_request('put', '/api/v1/userDataStream', request)
    #
    # def close_user_data_stream(self, listenKey):
    #     """
    #         Close out a user data stream.
    #     """
    #     request = {
    #             'listenKey': listenKey
    #         }
    #     return self.private_request('delete', '/api/v1/userDataStream', request)

    # #####################################
    # ##### Exchange specific methods #####
    # #####################################

    def public_get_formatted_best_books(self):
        book_ticker = self.public_get_ticker()
        results = {}
        for ticker in book_ticker:
            results[ticker["symbol"]] = {
                "Bid": ticker["bidPrice"],
                "BidQty": ticker["bidQty"],
                "Ask": ticker["askPrice"],
                "AskQty": ticker["askQty"]
            }
        return results

    def private_get_balances(self):
        return self.private_get_account_info().get('balances', [])

    # ############################################
    # ##### Exchange specific websockets API #####
    # ############################################

    def ws_init(self):
        self.ws_subscribe('!ticker@arr', self.ws_on_24hour_ticker_message)
        self._ws.run_forever()

    def ws_subscribe(self, channel, message_parser):
        """
            Subscibe to a channel
            The following <channel> values are supported:
            <symbol>@aggTrade - Aggregate Trade Streams
            <symbol>@trade - Trade Streams
            <symbol>@kline_<interval> - Kline/Candlestick Streams
            <symbol>@miniTicker - Individual Symbol Mini Ticker Stream
            !miniTicker@arr - All Market Mini Tickers Stream
            <symbol>@ticker - Individual Symbol Ticker Streams
            !ticker@arr - All Market Tickers Stream
            <symbol>@depth<levels> - Partial Book Depth Streams
            <symbol>@depth - Diff. Depth Stream
            Debug: ct['Poloniex'].ws_subscribe(1000)
        """
        self._ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/" + channel,
                                          on_message=message_parser,
                                          on_error=self.ws_on_error,
                                          on_close=self.ws_on_close,
                                          on_ping=self.ws_pong
                                          )

    def ws_pong(self, message):
        self._ws.send(message)

    def ws_on_24hour_ticker_message(self, message):
        parsed_message = json.loads(message)
        if isinstance(parsed_message, list):
            for market in parsed_message:
                try:
                    market_symbol = market['s']
                    self.update_market(
                        market_symbol,
                        {
                            'BaseVolume': float(market.get('q', 0)),
                            'CurrVolume': float(market.get('v', 0)),
                            'BestBid': float(market.get('b', 0)),
                            'BestAsk': float(market['a']),
                            'BestBidSize': float(market['B']),
                            'BestAskSize': float(market['A']),
                            '24HrHigh': float(market['h']),
                            '24HrLow': float(market['l']),
                            '24HrPercentMove': float(market['P']),
                            'LastTradedPrice': float(market['c']),
                            'TimeStamp': datetime.fromtimestamp(market['C'] / 1000),
                        }
                    )
                except Exception as e:
                    self.log_request_error(str(e))

    @staticmethod
    def ws_on_error(error):
        print("*** Binance websocket ERROR: ", error)

    def ws_on_close(self):
        print("### Binance websocket is closed ###")
        self.ws_init()

    # ###########################
    # ##### Generic methods #####
    # ###########################

    def get_consolidated_currency_definitions(self):
        """
            Loading currencies
            Debug: ct['Binance'].get_consolidated_currency_definitions()
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
        results = {}
        if isinstance(self._exchangeInfo['symbols'], list):
            for symbol in self._exchangeInfo['symbols']:
                try:
                    self._currencies[symbol['baseAsset']] = {
                        'Name': symbol['baseAsset'],
                        'DepositEnabled': True,
                        'WithdrawalEnabled': True,
                        'Notice': '',
                        'ExchangeBaseAddress': '',
                        'MinConfirmation': 0,
                        'WithdrawalFee': 0,
                        'WithdrawalMinAmount': 0,
                        'Precision': 0.00000001
                    }
                    if not symbol['quoteAsset'] in self._currencies:
                        self._currencies[symbol['quoteAsset']] = {
                            'Name': symbol['quoteAsset'],
                            'DepositEnabled': True,
                            'WithdrawalEnabled': True,
                            'Notice': '',
                            'ExchangeBaseAddress': '',
                            'MinConfirmation': 0,
                            'WithdrawalFee': 0,
                            'WithdrawalMinAmount': 0,
                            'Precision': 0.00000001
                        }
                except Exception as e:
                    self.log_request_error(str(e))

        return results

    def update_market_definitions(self, force_update=False):
        """
            Used to get the open and available trading markets at Binance along
            with other meta data.
            * force_update = False assumes that self._exchangeInfo was filled
            in recently enough
            Debug: ct['Binance'].update_market_definitions()
        """
        if isinstance(self._exchangeInfo['symbols'], list):
            for market in self._exchangeInfo['symbols']:
                try:
                    is_active = market.get('status', '') == 'TRADING'
                    is_restricted = not is_active
                    update_dict = {
                        'LocalBase':        market['quoteAsset'],
                        'LocalCurr':        market['baseAsset'],
                        'IsActive':         is_active,
                        'IsRestricted':     is_restricted,
                    }

                    for market_filter in market['filters']:
                        if market_filter.get('filterType', '') == 'PRICE_FILTER':
                            update_dict.update(
                                {
                                    'PriceMin':         float(market_filter['minPrice']),
                                    'PriceIncrement':   float(market_filter['tickSize']),
                                }
                            )
                        if market_filter.get('filterType', '') == 'LOT_SIZE':
                            update_dict.update(
                                {
                                    'BaseMinAmount':   0,
                                    'BaseIncrement':   pow(10, -market['quotePrecision']),
                                    'CurrMinAmount':   float(market_filter['minQty']),
                                    'CurrIncrement':   float(market_filter['stepSize']),
                                }
                            )

                    self.update_market(
                        market['symbol'],
                        update_dict
                    )
                except Exception as e:
                    self.log_request_error(str(e))

    def update_market_quotes(self):
        """
            Used to get the market quotes
            Debug: ct['Binance'].update_market_quotes()
        """
        book_ticker = self.public_get_ticker()
        if isinstance(book_ticker, list):
            for ticker in book_ticker:
                try:
                    market_symbol = ticker['symbol']
                    update_dict = {
                        'BestBid': float(ticker['bidPrice']),
                        'BestAsk': float(ticker['askPrice']),
                        'BestBidSize': float(ticker['bidQty']),
                        'BestAskSize': float(ticker['askQty']),
                    }
                    self.update_market(
                        market_symbol,
                        update_dict
                    )
                except Exception as e:
                    self.log_request_error(str(e))

    def update_market_24hrs(self):
        """
            Used to update 24-hour statistics
            Debug: ct['Binance'].update_market_24hr()
        """
        statistics = self.public_get_24hour_statistics()
        if isinstance(statistics, list):
            for market in statistics:
                try:
                    market_symbol = market['symbol']
                    self.update_market(
                        market_symbol,
                        {
                            'BaseVolume':       float(market.get('quoteVolume', 0)),
                            'CurrVolume':       float(market.get('volume', 0)),
                            'BestBid':          float(market['bidPrice']),
                            'BestAsk':          float(market['askPrice']),
                            'BestBidSize':      float(market['bidQty']),
                            'BestAskSize':      float(market['askQty']),
                            '24HrHigh':         float(market['highPrice']),
                            '24HrLow':          float(market['lowPrice']),
                            '24HrPercentMove':  float(market['priceChangePercent']),
                            'LastTradedPrice':  float(market['lastPrice']),
                            'TimeStamp':        datetime.fromtimestamp(market['closeTime'] / 1000),
                        }
                    )
                except Exception as e:
                    self.log_request_error(str(e))

    def get_consolidated_open_user_orders_in_market(self, market):
        """
            Used to retrieve outstanding orders
            Debug: ct['Binance'].get_consolidated_open_user_orders_in_market('LTCBTC')
        """
        open_orders = self.private_get_open_orders(market)
        results = []
        for order in open_orders:
            if order['side'] == 'BUY':
                order_type = 'Buy'
            else:
                order_type = 'Sell'

            results.append({
                'OrderId': order['orderId'],
                'OrderType': order_type,
                'OrderOpenedAt': datetime.fromtimestamp(market['time'] / 1000),
                'Price': float(order['price']),
                'Amount': float(order['origQty']),
                'Total': float(order['price']) * float(order['origQty']),
                'AmountRemaining': float(order['price']) * (float(order['origQty']) - float(order['executedQty'])),
            })
        return results

    def get_consolidated_recent_market_trades_per_market(self, market):
        """
            Used to update recent market trades at a given market
            Debug: ct['Binance'].update_recent_market_trades_per_market('LTCBTC')
        """
        trades = self.public_get_market_history(market)
        results = []
        for trade in trades:
            if trade['isBuyerMaker']:
                order_type = 'Buy'
            else:
                order_type = 'Sell'

            if float(trade['price']) > 0 and float(trade['qty']) > 0:
                results.append({
                    'TradeId': trade['id'],
                    'TradeType': order_type,
                    'TradeTime': datetime.fromtimestamp(trade['time'] / 1000),
                    'Price': float(trade['price']),
                    'Amount': float(trade['qty']),
                    'Total': float(trade['price']) * float(trade['qty'])
                })
        return results

    def get_consolidated_klines(self, market_symbol, interval='5m', lookback=None):
        """
            https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md
            [
              [
                1499040000000,      // Open time
                "0.01634790",       // Open
                "0.80000000",       // High
                "0.01575800",       // Low
                "0.01577100",       // Close
                "148976.11427815",  // Volume
                1499644799999,      // Close time
                "2434.19055334",    // Quote asset volume
                308,                // Number of trades
                "1756.87402397",    // Taker buy base asset volume
                "28.46694368",      // Taker buy quote asset volume
                "17928899.62484339" // Ignore.
              ]
            ]
        """
        load_chart = self.public_get_candlesticks(market_symbol, interval)
        results = []
        for i in load_chart:
            new_row = int(i[0] / 1000), float(i[1]), float(i[2]), float(i[3]), float(i[4]), float(i[5]), float(i[7])
            results.append(new_row)
        return results

    def get_consolidated_order_book(self, market, depth=5):
        raw_results = self.public_get_order_book(market, str(depth))
        take_bid = min(depth, len(raw_results['bids']))
        take_ask = min(depth, len(raw_results['asks']))

        results = {
            'Tradeable': 1,
            'Bid': {},
            'Ask': {}
        }
        for i in range(take_bid):
            results['Bid'][i] = {
                'Price': float(raw_results['bids'][i][0]),
                'Quantity': float(raw_results['bids'][i][1]),
            }
        for i in range(take_ask):
            results['Ask'][i] = {
                'Price': float(raw_results['asks'][i][0]),
                'Quantity': float(raw_results['asks'][i][1]),
            }

        return results

    def load_available_balances(self):
        available_balances = self.private_get_balances()
        self._available_balances = {}
        for balance in available_balances:
            currency = balance['asset']
            self._available_balances[currency] = float(balance["free"])
        return self._available_balances

    def load_balances_btc(self):
        balances = self.private_get_balances()
        self._complete_balances_btc = {}
        for balance in balances:
            currency = balance['asset']
            self._complete_balances_btc[currency] = {
                'Available': float(balance["free"]),
                'OnOrders': float(balance["locked"]),
                'Total': float(balance["free"]) + float(balance["locked"])
            }
        return self._complete_balances_btc

    def private_submit_new_order(self, direction, market, price, amount, trade_type):
        side = 'BUY'
        if direction == 'sell':
            side = 'SELL'

        time_in_force = 'GTC'
        if trade_type == 'ImmediateOrCancel':
            time_in_force = 'IOC'

        results = self.private_submit_trade(
            market,
            side,
            'LIMIT',
            amount,
            time_in_force,
            price,
            'RESULT'
        )

        return {
                'Amount': float(results['executedQty']),
                'OrderNumber': results['clientOrderId']
            }
