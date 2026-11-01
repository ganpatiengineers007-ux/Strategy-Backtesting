GTS LAB - 5 strategies (साफ़ फ़ाइलें)
इंस्टॉल:  unzip -o gts_lab_strategies.zip -d ~/gts_lab
जाँच:     cd ~/gts_lab && python3 -m py_compile *.py
चलाना:    python3 gamma_vwap_strategy.py data.csv     (data.csv न दो तो synthetic)
CSV: timestamp,open,high,low,close,volume [,max_gamma_strike,expiry_window]
#1 gamma_vwap_strategy.py (core engine भी)  #2 delta_vwap_strategy.py  #3 vega_iv_strategy.py
#4 theta_straddle_strategy.py  #5 greeks_confluence_strategy.py
