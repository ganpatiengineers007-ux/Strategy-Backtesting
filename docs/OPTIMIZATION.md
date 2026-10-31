# Optimization

Search sirf pehle 60% data par; chuna param baaki 40% HOLDOUT par parkha jaata hai.
Har trial `experiments.jsonl` me. Zyada trials = chance-luck ka khatra; `n_trials` hamesha dikhao.
CLI: `python -m cli.main optimize --strategy three_pm_momentum --data data/samples/sample_5m.csv --grid '{"stop_pct":[0.3,0.5],"target_pct":[0.8,1.0]}'`
