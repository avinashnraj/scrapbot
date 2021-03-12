import yaml

with open("config.yml", "r") as config_file:
    config = yaml.load(config_file, yaml.SafeLoader)

g_magic = config["settings"]["overall"]["magic"]
g_symbol = config["settings"]["overall"]["symbol"]

g_martingale_enable = config["settings"]["martingale"]["enable"]
g_level_spacing = config["settings"]["martingale"]["level_spacing"]
g_scale_factor = config["settings"]["martingale"]["scale_factor"]
g_level_maximum = config["settings"]["martingale"]["level_maximum"]

g_initial_volume = config["settings"]["money-management"]["initial_volume"]
g_stop_loss = config["settings"]["money-management"]["stop_loss"]
g_take_profit = config["settings"]["money-management"]["take_profit"]
g_min_total_profit = config["settings"]["money-management"]["minimum_total_profit"]

g_token = config["settings"]["connection"]["token"]

g_enable_sl_trailing = config["settings"]["trailing"]["enable"]
g_trailing_start = config["settings"]["trailing"]["trailing_start"]
g_trailing_step = config["settings"]["trailing"]["trailing_step"]

g_enable_sl_to_open = config["settings"]["sl_to_open"]["enable"]
g_sl_to_open_total_profit = config["settings"]["sl_to_open"]["total_profit"]

# Available periods : 'm1', 'm5', 'm15', 'm30', 'H1', 'H4'
g_signal_open_type = config["settings"]["signals"]["open_type"]
g_signal_close_type = config["settings"]["signals"]["close_type"]
g_time_frame = config["settings"]["signals"]["time_frame"]
g_fast_sma_periods = config["settings"]["signals"]["ema"]["fast_sma_periods"]
g_slow_sma_periods = config["settings"]["signals"]["ema"]["slow_sma_periods"]
g_fast_sma_shift = config["settings"]["signals"]["ema"]["fast_sma_shift"]
g_slow_sma_shift = config["settings"]["signals"]["ema"]["slow_sma_shift"]
g_rsi_period = config["settings"]["signals"]["rsi"]["period"]
g_rsi_max = config["settings"]["signals"]["rsi"]["max"]
g_rsi_min = config["settings"]["signals"]["rsi"]["min"]

g_number_of_candles = config["settings"]["signals"]["number_of_candles"]