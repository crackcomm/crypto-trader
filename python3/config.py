WINDOW_SIZE = {
    'left':     50,
    'top':      50,
    'width':    1700,
    'height':   1000,
}
DISPLAY_BOOK_DEPTH = 5
API_KEYS ={
    'Binance': {
        'APIKey': '',
        'Secret': ''
    },
    'Bittrex': {
        'APIKey': '',
        'Secret': ''
    },
    'Kucoin': {
        'APIKey': '',
        'Secret': ''
    },
    'Poloniex': {
        'APIKey': '',
        'Secret': ''
    },
}
EXCHANGES_TO_LOAD = [
    'Binance',
    'Bittrex',
    'Coinbase',
    'Hotbit',
    'Kucoin',
    'Poloniex'
]
EXCHANGE_CURRENCY_RENAME_MAP = {
    'Bittrex':  {
                    'BITS': 'BITS_BITSWIFT',
                },
    'Poloniex': {
                    'BITS': 'BITS_BITSTAR',
                    'BTM': 'BTM_BITMARK',
                    'STR': 'XLM',
                    'APH': 'APH_APHRODITE'
                },
    'Binance':  {
                    'BCC': 'BCH'
                },
    'Kucoin':   {
                    'CPC': 'CPC_CPCHAIN'
                },
}
HOME_VIEW_EXCHANGE = 'Bittrex'
HOME_VIEW_BASE_CODE = 'USD'
HOME_VIEW_CURRENCY_CODE = 'BTC'
HOME_VIEW_CHART_INTERVAL = '15 Minutes'
HOME_VIEW_CHART_LOOKBACK = '1 Day'
