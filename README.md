STRATEGY VALIDATION LAB

Complete Repository Architecture & Engineering Blueprint v1.0

प्रोजेक्ट का प्रकार: बहुभाषी ट्रेडिंग रणनीति अनुसंधान, बैकटेस्टिंग, सत्यापन एवं प्रदर्शन विश्लेषण प्लेटफॉर्म।

प्राथमिक उद्देश्य: किसी भी समर्थित ट्रेडिंग रणनीति को एक मानकीकृत प्रक्रिया से गुजारना, उसके परिणामों का स्वतंत्र सत्यापन करना और साक्ष्य-आधारित रिपोर्ट तैयार करना।

प्रस्तावित रिपॉजिटरी का नाम: "strategy-validation-lab"

प्रस्तावित संस्करण: "1.0.0"

मुख्य भाषाएँ: Python, Go, TypeScript, HTML, CSS, JavaScript, SQL, C++ और Rust।

अतिरिक्त तकनीकें: PostgreSQL, Parquet, Protobuf, OpenAPI, Docker और CI/CD।

संचालन नीति: Research First, Reproducible Testing, Risk-Controlled Validation, No Automatic Live Execution.

---

1. प्रोजेक्ट का मुख्य उद्देश्य

यह सिस्टम निम्नलिखित कार्य करेगा:

1. नई रणनीति को रजिस्ट्री में पंजीकृत करना।
2. रणनीति के आवश्यक डेटा और पैरामीटर की जाँच करना।
3. ऐतिहासिक बाजार डेटा को सत्यापित करना।
4. रणनीति के संकेत उत्पन्न करना।
5. ऐतिहासिक बैकटेस्ट चलाना।
6. ब्रोकरेज, स्लिपेज और अन्य लागू लागतों की गणना करना।
7. पोज़िशन साइज़, स्टॉप-लॉस और जोखिम की गणना करना।
8. Win Rate, Accuracy, Expectancy, Profit Factor और Drawdown निकालना।
9. Out-of-Sample, Walk-Forward और Robustness परीक्षण चलाना।
10. Look-Ahead Bias, Data Leakage और Overfitting की जाँच करना।
11. प्रत्येक परीक्षण के लिए पुनरुत्पादित रिपोर्ट तैयार करना।
12. HTML डैशबोर्ड पर परिणाम प्रदर्शित करना।
13. रणनीतियों के प्रदर्शन की एक-दूसरे से तुलना करना।
14. सफल परीक्षणों के प्रमाण और संस्करण सुरक्षित रखना।
15. आवश्यक स्वीकृति के बिना किसी रणनीति को लाइव ट्रेडिंग में प्रवेश न देना।

यह प्लेटफॉर्म रणनीतियों की जाँच करेगा। यह अपने आप लाभप्रदता की गारंटी नहीं देगा।

---

2. संपूर्ण सिस्टम आर्किटेक्चर

                 STRATEGY VALIDATION LAB
                           |
             +-------------+-------------+
             |                           |
       FRONTEND LAYER               BACKEND LAYER
             |                           |
     HTML / CSS / TypeScript       Python / Go
             |                           |
       Web Dashboard              API Gateway
             |                           |
             +-------------+-------------+
                           |
                    STRATEGY REGISTRY
                           |
              Strategy Contract Validation
                           |
              +------------+-------------+
              |                          |
        DATA VALIDATION            STRATEGY ENGINE
              |                          |
              +------------+-------------+
                           |
                  BACKTEST ENGINE
                           |
             +-------------+-------------+
             |             |              |
         EXECUTION       RISK         PORTFOLIO
          MODEL         ENGINE         ENGINE
             |             |              |
             +-------------+--------------+
                           |
                 VALIDATION ENGINE
                           |
             +-------------+-------------+
             |             |             |
          WALK-FWD     OUT-OF-SAMPLE   ROBUSTNESS
             |             |             |
             +-------------+-------------+
                           |
                  METRICS ENGINE
                           |
                  REPORT GENERATOR
                           |
             +-------------+-------------+
             |                           |
         HTML REPORTS               JSON / CSV
             |                           |
             +-------------+-------------+
                           |
                  ARTIFACT STORAGE
                           |
             +-------------+-------------+
             |                           |
        PostgreSQL                 Parquet / Files
             |
          Audit Log

C++ और Rust को शुरुआती संस्करण में मुख्य Python इंजन के विकल्प के रूप में इस्तेमाल नहीं किया जाएगा। इन्हें आवश्यकता सिद्ध होने पर विशिष्ट, परीक्षण-आधारित प्रदर्शन सुधार के लिए जोड़ा जाएगा।

---

3. पूरी रिपॉजिटरी की डायरेक्टरी संरचना

यह प्रस्तावित पूर्ण संरचना है। इसमें लगभग 120–150 फाइलों तक विस्तार करने की गुंजाइश है। सभी फाइलें पहले दिन बनाना आवश्यक नहीं है।

strategy-validation-lab/
│
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── pyproject.toml
├── requirements.lock
├── go.mod
├── Makefile
├── .gitignore
├── .env.example
├── .editorconfig
├── .pre-commit-config.yaml
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── REPOSITORY_MAP.md
│   ├── STRATEGY_CONTRACT.md
│   ├── DATA_CONTRACT.md
│   ├── BACKTEST_ENGINE.md
│   ├── VALIDATION_POLICY.md
│   ├── METRICS_DICTIONARY.md
│   ├── SECURITY_POLICY.md
│   ├── TESTING_POLICY.md
│   ├── DEPLOYMENT.md
│   ├── DECISION_GATES.md
│   └── adr/
│       ├── ADR-001-LANGUAGE-BOUNDARIES.md
│       ├── ADR-002-DATA-CONTRACTS.md
│       └── ADR-003-EXECUTION-MODEL.md
│
├── config/
│   ├── system.yaml
│   ├── data.yaml
│   ├── backtest.yaml
│   ├── risk.yaml
│   ├── costs.yaml
│   ├── validation.yaml
│   ├── reporting.yaml
│   └── logging.yaml
│
├── contracts/
│   ├── strategy.schema.json
│   ├── data.schema.json
│   ├── signal.schema.json
│   ├── trade.schema.json
│   ├── report.schema.json
│   ├── run.schema.json
│   ├── openapi.yaml
│   └── proto/
│       ├── common.proto
│       ├── market_data.proto
│       ├── strategy.proto
│       ├── signal.proto
│       ├── backtest.proto
│       ├── metrics.proto
│       └── report.proto
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── public/
│   │   ├── favicon.svg
│   │   └── logo.svg
│   └── src/
│       ├── main.ts
│       ├── app.ts
│       ├── styles/
│       │   ├── base.css
│       │   ├── layout.css
│       │   ├── components.css
│       │   └── dashboard.css
│       ├── api/
│       │   ├── client.ts
│       │   ├── strategies.ts
│       │   ├── backtests.ts
│       │   ├── reports.ts
│       │   └── health.ts
│       ├── components/
│       │   ├── navigation.ts
│       │   ├── data-table.ts
│       │   ├── metric-card.ts
│       │   ├── chart-panel.ts
│       │   ├── status-badge.ts
│       │   └── error-panel.ts
│       ├── pages/
│       │   ├── dashboard.ts
│       │   ├── strategy-registry.ts
│       │   ├── strategy-detail.ts
│       │   ├── create-strategy.ts
│       │   ├── backtest-runs.ts
│       │   ├── backtest-detail.ts
│       │   ├── validation-results.ts
│       │   ├── comparison.ts
│       │   ├── reports.ts
│       │   ├── datasets.ts
│       │   ├── system-health.ts
│       │   └── audit-log.ts
│       ├── charts/
│       │   ├── equity-curve.ts
│       │   ├── drawdown-chart.ts
│       │   ├── monthly-returns.ts
│       │   └── trade-distribution.ts
│       └── types/
│           ├── strategy.ts
│           ├── backtest.ts
│           ├── metrics.ts
│           └── report.ts
│
├── backend/
│   ├── app.py
│   ├── dependencies.py
│   ├── api/
│   │   ├── health.py
│   │   ├── strategies.py
│   │   ├── backtests.py
│   │   ├── validation.py
│   │   ├── reports.py
│   │   ├── datasets.py
│   │   └── comparisons.py
│   ├── services/
│   │   ├── strategy_service.py
│   │   ├── backtest_service.py
│   │   ├── validation_service.py
│   │   ├── report_service.py
│   │   └── dataset_service.py
│   ├── schemas/
│   │   ├── strategy.py
│   │   ├── backtest.py
│   │   ├── validation.py
│   │   └── report.py
│   ├── middleware/
│   │   ├── request_id.py
│   │   ├── error_handler.py
│   │   └── authentication.py
│   └── jobs/
│       ├── queue.py
│       ├── worker.py
│       └── job_status.py
│
├── registry/
│   ├── registry.py
│   ├── metadata.py
│   ├── lifecycle.py
│   ├── versioning.py
│   ├── compatibility.py
│   ├── permissions.py
│   └── storage.py
│
├── strategies/
│   ├── base.py
│   ├── context.py
│   ├── models.py
│   ├── validation.py
│   ├── examples/
│   │   ├── example_strategy.py
│   │   └── example_strategy.yaml
│   ├── gamma_blast/
│   │   ├── strategy.py
│   │   ├── config.yaml
│   │   └── manifest.yaml
│   └── three_pm_momentum/
│       ├── strategy.py
│       ├── config.yaml
│       └── manifest.yaml
│
├── data/
│   ├── models.py
│   ├── loaders.py
│   ├── normalizer.py
│   ├── validators.py
│   ├── quality_report.py
│   ├── timestamps.py
│   ├── corporate_actions.py
│   ├── survivorship.py
│   ├── storage.py
│   └── sources/
│       ├── csv_source.py
│       ├── parquet_source.py
│       └── broker_source.py
│
├── indicators/
│   ├── trend.py
│   ├── momentum.py
│   ├── volatility.py
│   ├── volume.py
│   ├── market_structure.py
│   └── options_greeks.py
│
├── backtest/
│   ├── engine.py
│   ├── clock.py
│   ├── event_queue.py
│   ├── portfolio.py
│   ├── orders.py
│   ├── fills.py
│   ├── execution.py
│   ├── slippage.py
│   ├── fees.py
│   ├── position_sizing.py
│   ├── stop_manager.py
│   ├── accounting.py
│   └── results.py
│
├── risk/
│   ├── manager.py
│   ├── limits.py
│   ├── exposure.py
│   ├── drawdown.py
│   └── kill_switch.py
│
├── validation/
│   ├── pipeline.py
│   ├── leakage_checks.py
│   ├── out_of_sample.py
│   ├── walk_forward.py
│   ├── cross_validation.py
│   ├── overfitting.py
│   ├── robustness.py
│   ├── regime_analysis.py
│   └── statistical_confidence.py
│
├── metrics/
│   ├── accuracy.py
│   ├── expectancy.py
│   ├── trade_metrics.py
│   ├── risk_metrics.py
│   ├── return_metrics.py
│   ├── benchmarks.py
│   └── confidence_intervals.py
│
├── optimization/
│   ├── parameter_search.py
│   ├── constraints.py
│   └── experiment_tracking.py
│
├── reporting/
│   ├── generator.py
│   ├── html_report.py
│   ├── json_report.py
│   ├── csv_export.py
│   ├── charts.py
│   └── templates/
│       └── report.html
│
├── persistence/
│   ├── database.py
│   ├── models.py
│   ├── repositories.py
│   ├── migrations/
│   └── audit.py
│
├── observability/
│   ├── logging.py
│   ├── metrics.py
│   ├── tracing.py
│   └── health.py
│
├── cli/
│   ├── main.py
│   ├── commands.py
│   └── formatting.py
│
├── engines/
│   ├── go/
│   │   ├── cmd/
│   │   │   └── validator/
│   │   │       └── main.go
│   │   ├── internal/
│   │   │   ├── contracts/
│   │   │   ├── validation/
│   │   │   ├── jobs/
│   │   │   └── observability/
│   │   └── README.md
│   ├── cpp/
│   │   ├── CMakeLists.txt
│   │   ├── include/
│   │   │   └── svl/
│   │   │       └── rolling_stats.hpp
│   │   ├── src/
│   │   │   └── rolling_stats.cpp
│   │   ├── tests/
│   │   │   └── test_rolling_stats.cpp
│   │   └── README.md
│   └── rust/
│       ├── Cargo.toml
│       ├── src/
│       │   └── lib.rs
│       ├── tests/
│       │   └── contract_tests.rs
│       └── README.md
│
├── tests/
│   ├── unit/
│   │   ├── test_data.py
│   │   ├── test_registry.py
│   │   ├── test_backtest.py
│   │   ├── test_metrics.py
│   │   └── test_risk.py
│   ├── integration/
│   │   ├── test_strategy_pipeline.py
│   │   ├── test_api.py
│   │   └── test_report_pipeline.py
│   ├── regression/
│   │   └── test_known_results.py
│   ├── property/
│   │   └── test_accounting_invariants.py
│   ├── performance/
│   │   └── test_benchmark.py
│   ├── fixtures/
│   │   ├── sample_ohlcv.csv
│   │   └── expected_results.json
│   ├── test_no_lookahead.py
│   ├── test_reproducibility.py
│   └── test_execution_costs.py
│
├── scripts/
│   ├── validate_repo.sh
│   ├── run_tests.sh
│   ├── run_backtest.sh
│   ├── build_frontend.sh
│   └── generate_report.sh
│
├── infra/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── nginx.conf
│   └── ci/
│       └── pipeline.yml
│
├── artifacts/
│   └── .gitkeep
│
└── output/
    └── .gitkeep

महत्वपूर्ण: "artifacts/" और "output/" में वास्तविक परीक्षण परिणाम, बड़े डेटा सेट और निजी जानकारी बिना समीक्षा के Git में जमा नहीं करनी चाहिए। इनकी नीति ".gitignore" और संग्रहण व्यवस्था में निर्धारित होनी चाहिए।

---

4. HTML, Frontend और Backend का स्पष्ट विभाजन

4.1 HTML में क्या आएगा?

मुख्य प्रवेश फाइल:

"frontend/index.html"

इसमें केवल वेब एप्लिकेशन का मूल ढाँचा होगा। पूरी बैकटेस्टिंग या रणनीति की गणना HTML में नहीं होगी।

रिपोर्ट के लिए अलग फाइल:

"reporting/templates/report.html"

इसका उपयोग प्रत्येक बैकटेस्ट की HTML रिपोर्ट तैयार करने में होगा।

HTML की जिम्मेदारियाँ:

- पेज का मूल ढाँचा।
- डैशबोर्ड के कंटेनर।
- चार्ट और टेबल के स्थान।
- नेविगेशन संरचना।
- रिपोर्ट के लिए प्रस्तुति टेम्पलेट।

4.2 CSS और TypeScript में क्या आएगा?

"frontend/src/styles/"

यहाँ डैशबोर्ड की डिजाइन, लेआउट, रंग, टेबल और कार्ड का रूप निर्धारित होगा।

"frontend/src/pages/"

यहाँ अलग-अलग पेजों का व्यवहार होगा।

प्रस्तावित पेज:

1. Dashboard
2. Strategy Registry
3. Strategy Details
4. Add Strategy
5. Backtest Runs
6. Backtest Details
7. Validation Results
8. Strategy Comparison
9. Reports
10. Datasets
11. System Health
12. Audit Log

"frontend/src/api/"

यहाँ फ्रंटएंड और बैकएंड के बीच API संचार होगा।

फ्रंटएंड स्वयं Win Rate, Profit Factor या वास्तविक बैकटेस्ट परिणाम तय नहीं करेगा। वह बैकएंड द्वारा लौटाए गए और सत्यापित परिणाम दिखाएगा।

4.3 Python Backend में क्या आएगा?

मुख्य फाइल:

"backend/app.py"

इसमें API एप्लिकेशन शुरू होगा।

प्रस्तावित API:

Endpoint| काम
"GET /health"| सिस्टम की स्थिति
"GET /strategies"| पंजीकृत रणनीतियों की सूची
"POST /strategies"| रणनीति पंजीकरण का अनुरोध
"GET /strategies/{id}"| रणनीति का विवरण
"POST /backtests"| बैकटेस्ट शुरू करना
"GET /backtests/{id}"| बैकटेस्ट की स्थिति
"GET /backtests/{id}/results"| बैकटेस्ट परिणाम
"POST /validations"| सत्यापन प्रक्रिया शुरू करना
"GET /validations/{id}"| सत्यापन रिपोर्ट
"GET /reports/{id}"| रिपोर्ट प्राप्त करना
"GET /datasets"| उपलब्ध डेटा सेट
"POST /comparisons"| रणनीतियों की तुलना

API को FastAPI जैसी लाइब्रेरी से बनाया जा सकता है। अंतिम तकनीकी चयन "pyproject.toml" और आर्किटेक्चर निर्णय में दर्ज होगा।

लंबे बैकटेस्ट को HTTP अनुरोध के अंदर लगातार चलाने के बजाय जॉब क्यू और वर्कर के माध्यम से चलाना बेहतर होगा।

---

5. Strategy Registry का पूरा डिजाइन

यह इस सिस्टम का केंद्रीय हिस्सा होगा।

मुख्य फाइल:

"registry/registry.py"

सहायक फाइलें:

- "registry/metadata.py"
- "registry/lifecycle.py"
- "registry/versioning.py"
- "registry/compatibility.py"
- "registry/permissions.py"
- "registry/storage.py"

हर रणनीति के लिए निम्न जानकारी आवश्यक होगी:

फ़ील्ड| उदाहरण
Strategy ID| "gamma_blast"
Version| "1.0.0"
Name| Gamma Blast
Asset Class| Options
Market| NIFTY
Timeframe| 5 minutes
Required Data| OHLCV, Option Chain, OI
Parameters| रणनीति के कॉन्फ़िगर किए जाने वाले मान
Signal Contract| मानकीकृत संकेत संरचना
Risk Profile| अनुमत जोखिम नियम
Status| Draft, Validated, Rejected
Source Hash| परीक्षण किए गए कोड की पहचान
Created At| पंजीकरण समय
Validation Run ID| संबंधित सत्यापन रन

हर रणनीति के लिए "manifest.yaml" होगा।

उदाहरण:

strategy:
  id: gamma_blast
  version: 1.0.0
  entrypoint: strategies.gamma_blast.strategy:GammaBlastStrategy

market:
  asset_class: options
  symbols:
    - NIFTY
  timeframe: 5m

data_requirements:
  - spot_ohlcv
  - option_chain
  - open_interest

execution:
  mode: historical_backtest

validation:
  require_data_quality_check: true
  require_no_lookahead_check: true
  require_out_of_sample: true
  require_cost_model: true

live_trading:
  enabled: false

यह उदाहरण प्रारंभिक अनुबंध है। वास्तविक रणनीति के अनुसार आवश्यक डेटा और पैरामीटर तय होंगे।

सुरक्षा नियम: किसी नई Python रणनीति को केवल Registry में पंजीकृत होने के कारण सीधे आयात करके मुख्य प्रक्रिया में चलाना सुरक्षित नहीं है। अनधिकृत कोड के निष्पादन से बचने के लिए अलग प्रक्रिया, सीमित अनुमतियाँ और संसाधन सीमाएँ लागू करनी होंगी।

---

6. Python Strategy Engine

मुख्य फाइलें:

- "strategies/base.py"
- "strategies/context.py"
- "strategies/models.py"
- "strategies/validation.py"

हर रणनीति को एक साझा इंटरफेस का पालन करना होगा।

सामान्य प्रक्रिया:

Strategy Manifest
       |
       v
Schema Validation
       |
       v
Data Requirements Check
       |
       v
Strategy Initialization
       |
       v
Signal Generation
       |
       v
Signal Contract Validation
       |
       v
Backtest Engine

एक रणनीति में प्रयुक्त पैरामीटर स्पष्ट होने चाहिए। उदाहरण के लिए, यदि किसी रणनीति को ATR चाहिए, तो वह इसकी अवधि, गणना विधि और आवश्यक ऐतिहासिक डेटा घोषित करेगी।

इसी तरह, ऑप्शन रणनीति को यदि Greeks या Open Interest चाहिए, तो केवल OHLCV डेटा उपलब्ध होने पर सिस्टम उसे सफलतापूर्वक सत्यापित घोषित नहीं करेगा।

---

7. Data Engine

मुख्य डायरेक्टरी:

"data/"

इसका उद्देश्य है कि हर रणनीति को एक समान और सत्यापित प्रारूप में डेटा मिले।

प्रमुख फाइलों की जिम्मेदारियाँ:

फाइल| जिम्मेदारी
"models.py"| डेटा संरचनाएँ
"loaders.py"| डेटा लोड करना
"normalizer.py"| सामान्य प्रारूप में बदलना
"validators.py"| डेटा की गुणवत्ता जाँचना
"quality_report.py"| डेटा गुणवत्ता रिपोर्ट
"timestamps.py"| टाइमस्टैम्प और समय क्षेत्र
"corporate_actions.py"| लागू कॉर्पोरेट कार्रवाइयों का प्रबंधन
"survivorship.py"| Survivorship Bias से जुड़े जोखिमों की जाँच
"storage.py"| डेटा संग्रहण
"sources/csv_source.py"| CSV स्रोत
"sources/parquet_source.py"| Parquet स्रोत
"sources/broker_source.py"| ब्रोकर डेटा एडेप्टर

डेटा सत्यापन में ये जाँच आवश्यक होंगी:

- गलत या डुप्लिकेट टाइमस्टैम्प।
- अनुपस्थित OHLCV मान।
- गलत OHLC संबंध।
- गलत समय क्षेत्र।
- असंगत प्रतीक या इंस्ट्रूमेंट पहचान।
- अनुपस्थित ऑप्शन कॉन्ट्रैक्ट विवरण।
- ऐतिहासिक डेटा में अनजाने भविष्य के मान।
- डेटा सेट की अवधि और पूर्णता।

डेटा स्रोतों को इस प्रकार बनाया जाए कि भविष्य में Dhan, FYERS या अन्य अनुमत स्रोत जोड़े जा सकें। शुरुआती संस्करण में वास्तविक ब्रोकर कनेक्शन अनिवार्य नहीं है।

---

8. Backtest Engine

मुख्य फाइल:

"backtest/engine.py"

सहायक मॉड्यूल:

फाइल| काम
"clock.py"| समय-आधारित घटनाओं का क्रम
"event_queue.py"| घटनाओं का प्रबंधन
"portfolio.py"| पोर्टफोलियो स्थिति
"orders.py"| ऑर्डर मॉडल
"fills.py"| ऑर्डर निष्पादन के परिणाम
"execution.py"| निष्पादन नियम
"slippage.py"| स्लिपेज मॉडल
"fees.py"| ब्रोकरेज और अन्य लागत
"position_sizing.py"| पोज़िशन साइज़
"stop_manager.py"| स्टॉप-लॉस प्रबंधन
"accounting.py"| लाभ, हानि और पूँजी गणना
"results.py"| बैकटेस्ट परिणाम

इंजन को समय के क्रम में चलना चाहिए। किसी रणनीति को उस समय उपलब्ध न हुई जानकारी से ट्रेड करने की अनुमति नहीं होनी चाहिए।

इसके अतिरिक्त, यदि एक ही OHLC कैंडल में Stop Loss और Target दोनों छूते दिखाई दें, तो इंजन मनमाने ढंग से लाभकारी परिणाम नहीं चुन सकता। उसे अधिक सूक्ष्म डेटा या स्पष्ट और रूढ़िवादी निष्पादन नियम का उपयोग करना होगा।

ऑप्शन बैकटेस्ट में एक्सपायरी, लॉट साइज़, कॉन्ट्रैक्ट की उपलब्धता, Bid-Ask Spread, प्रीमियम और आवश्यक Greeks का मॉडल भी उपयुक्त होना चाहिए।

---

9. Risk Engine

मुख्य डायरेक्टरी:

"risk/"

फाइलें:

- "manager.py"
- "limits.py"
- "exposure.py"
- "drawdown.py"
- "kill_switch.py"

यह मॉड्यूल निम्न काम करेगा:

1. प्रति ट्रेड निर्धारित जोखिम की जाँच।
2. पोज़िशन साइज़ की सीमा।
3. कुल पोर्टफोलियो एक्सपोज़र।
4. अधिकतम Drawdown की निगरानी।
5. एक साथ खुले जोखिमों का आकलन।
6. निर्धारित सीमा टूटने पर परीक्षण रोकना।
7. ट्रेडिंग के लिए स्वीकृत जोखिम सीमाओं का रिकॉर्ड रखना।

यहाँ एक महत्वपूर्ण अंतर होगा: बैकटेस्ट में Stop Loss होना और किसी वास्तविक ऑर्डर का उसी मूल्य पर निष्पादित होना अलग बातें हैं। Gap, Spread और Slippage के कारण वास्तविक नुकसान अनुमान से अधिक हो सकता है।

---

10. Validation Engine

मुख्य फाइल:

"validation/pipeline.py"

सहायक फाइलें:

- "leakage_checks.py"
- "out_of_sample.py"
- "walk_forward.py"
- "cross_validation.py"
- "overfitting.py"
- "robustness.py"
- "regime_analysis.py"
- "statistical_confidence.py"

इस इंजन का काम केवल लाभ मापना नहीं, बल्कि यह देखना है कि लाभ का दावा कितना विश्वसनीय है।

आवश्यक परीक्षण

A. Data Leakage

क्या भविष्य की जानकारी किसी संकेत या निर्णय में इस्तेमाल हुई?

B. Out-of-Sample

क्या रणनीति ने उन डेटा पर भी काम किया जिन्हें पैरामीटर चुनने में उपयोग नहीं किया गया था?

C. Walk-Forward

क्या अलग-अलग समय खंडों में प्रदर्शन स्वीकार्य रहा?

D. Overfitting

क्या अत्यधिक पैरामीटर खोज के कारण केवल ऐतिहासिक डेटा पर अच्छा परिणाम मिला?

E. Cost Sensitivity

यदि स्लिपेज या निष्पादन लागत बढ़ जाए, तो रणनीति का प्रदर्शन कितना बदलता है?

F. Regime Analysis

क्या रणनीति अलग-अलग बाजार स्थितियों में भी उचित प्रदर्शन करती है?

G. Statistical Confidence

क्या ट्रेडों की संख्या इतनी है कि Win Rate और Expectancy के अनुमान पर उचित विश्वास किया जा सके?

इन परीक्षणों के बिना किसी रणनीति को केवल ऐतिहासिक लाभ के आधार पर सफल घोषित नह
