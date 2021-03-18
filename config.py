import yaml

with open("config.yml", "r") as config_file:
    config = yaml.load(config_file, yaml.SafeLoader)

g_symbols = config["settings"]["overall"]["symbols"]
g_magic = dict()
g_symbol = dict()

g_martingale_enable = dict()
g_level_spacing = dict()
g_scale_factor = dict()
g_level_maximum = dict()

g_initial_volume = dict()
g_stop_loss = dict()
g_take_profit = dict()
g_min_total_profit = dict()

g_token = dict()

g_enable_sl_trailing = dict()
g_trailing_start = dict()
g_trailing_step = dict()

g_enable_sl_to_open = dict()
g_sl_to_open_total_profit = dict()

# Available periods : 'm1', 'm5', 'm15', 'm30', 'H1', 'H4'
g_signal_open_type = dict()
g_signal_close_type = dict()
g_time_frame = dict()
g_fast_sma_periods = dict()
g_slow_sma_periods = dict()
g_fast_sma_shift = dict()
g_slow_sma_shift = dict()
g_rsi_period = dict()
g_rsi_max = dict()
g_rsi_min = dict()
g_gap_distance = dict()
g_trade_on_close = dict()

g_number_of_candles = dict()

g_logger_enable = dict()
for symbol in g_symbols:
    with open("config-" + symbol.lower() + ".yml", "r") as config_file:
        config = yaml.load(config_file, yaml.SafeLoader)

    g_magic[symbol] = config["settings"]["overall"]["magic"]
    g_symbol[symbol] = config["settings"]["overall"]["symbol"]

    g_martingale_enable[symbol] = config["settings"]["martingale"]["enable"]
    g_level_spacing[symbol] = config["settings"]["martingale"]["level_spacing"]
    g_scale_factor[symbol] = config["settings"]["martingale"]["scale_factor"]
    g_level_maximum[symbol] = config["settings"]["martingale"]["level_maximum"]

    g_initial_volume[symbol] = config["settings"]["money-management"]["initial_volume"]
    g_stop_loss[symbol] = config["settings"]["money-management"]["stop_loss"]
    g_take_profit[symbol] = config["settings"]["money-management"]["take_profit"]
    g_min_total_profit[symbol] = config["settings"]["money-management"]["minimum_total_profit"]

    g_token[symbol] = config["settings"]["connection"]["token"]

    g_enable_sl_trailing[symbol] = config["settings"]["trailing"]["enable"]
    g_trailing_start[symbol] = config["settings"]["trailing"]["trailing_start"]
    g_trailing_step[symbol] = config["settings"]["trailing"]["trailing_step"]

    g_enable_sl_to_open[symbol] = config["settings"]["sl_to_open"]["enable"]
    g_sl_to_open_total_profit[symbol] = config["settings"]["sl_to_open"]["total_profit"]

    # Available periods : 'm1', 'm5', 'm15', 'm30', 'H1', 'H4'
    g_signal_open_type[symbol] = config["settings"]["signals"]["open_type"]
    g_signal_close_type[symbol] = config["settings"]["signals"]["close_type"]
    g_time_frame[symbol] = config["settings"]["signals"]["time_frame"]
    g_fast_sma_periods[symbol] = config["settings"]["signals"]["ema"]["fast_sma_periods"]
    g_slow_sma_periods[symbol] = config["settings"]["signals"]["ema"]["slow_sma_periods"]
    g_fast_sma_shift[symbol] = config["settings"]["signals"]["ema"]["fast_sma_shift"]
    g_slow_sma_shift[symbol] = config["settings"]["signals"]["ema"]["slow_sma_shift"]
    g_rsi_period[symbol] = config["settings"]["signals"]["rsi"]["period"]
    g_rsi_max[symbol] = config["settings"]["signals"]["rsi"]["max"]
    g_rsi_min[symbol] = config["settings"]["signals"]["rsi"]["min"]
    g_gap_distance[symbol] = config["settings"]["signals"]["gap"]["distance"]

    g_number_of_candles[symbol] = config["settings"]["signals"]["number_of_candles"]
    g_trade_on_close[symbol] = config["settings"]["overall"]["trade_on_close"]

    g_logger_enable[symbol] = config["settings"]["logging"]["enable"]
