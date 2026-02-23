# pyjpboatrace Manifesto

## 📂 ディレクトリ構成図

プロジェクト全体のディレクトリ構成は以下のようになっています。

```text
.
├── .venv/                      # Python仮想環境
├── data/                       # 【データセット】
│   ├── races.csv               # レース基本情報 (Phase 1出力)
│   ├── entries.csv             # 出走表データ (Phase 1出力)
│   ├── results.csv             # レース結果 (Phase 1出力)
│   ├── training_base.csv       # 学習用ベースデータ (Phase 2出力)
│   ├── training_featured.csv   # 特徴量エンジニアリング済みデータ (Phase 3出力)
│   └── model.pkl               # 学習済みモデル (Phase 4出力)
├── src/                        # 【データパイプライン】 (予測AI開発本番用)
│   ├── collect_data_phase1.py        # Phase 1: データ収集スクリプト
│   ├── transform_data_phase2.py      # Phase 2: データ変換・結合スクリプト
│   ├── feature_engineering_phase3.py # Phase 3: 特徴量生成スクリプト
│   └── train_model_phase4.py         # Phase 4: モデル学習・評価スクリプト
├── tempt_tests_sandbox/        # 【旧・実験用スクリプト】 (アーカイブ)
│   ├── collect_training_data.py
│   ├── train_model.py
│   └── ...
├── pyjpboatrace/               # 【ボートレースライブラリ】 (外部ツール)
│   ├── README.md               # 説明書
│   ├── pyproject.toml          # ライブラリ設定
│   ├── pyjpboatrace/           # ソースコード本体
│   │   ├── pyjpboatrace.py     # 司令塔クラス
│   │   ├── scraper/            # スクレイパー群
│   │   │   ├── stadiums_scraper.py
│   │   │   ├── races_scraper.py
│   │   │   ├── result_scraper.py
│   │   │   └── ...
│   │   ├── operator/           # オペレーター群
│   │   │   ├── better.py
│   │   │   └── ...
│   │   └── ...
│   └── tests/                  # テストコード
│       ├── scraper/
│       ├── operator/
│       └── ...
├── PROJECT5.md                 # 要件定義書・プロジェクト計画
├── manifesto.md                # 構成図 (本書)
├── pyproject.toml              # プロジェクト設定 (uv管理)
├── uv.lock                     # 依存ライブラリのロックファイル
└── README.md
```

## 📝 各ファイルの役割解説

### 1. プロジェクトルート (一番上の階層)
| ファイル名 | 役割 |
| :--- | :--- |
| `README.md` | このツールの取扱説明書です。最初に読むべき情報が書いてあります。 |
| `pyproject.toml` | Pythonなどの設定ファイルです。必要なライブラリやバージョンが書かれています。 |
| `download_html_for_test.sh` | テストに使うためのWebページのコピーをダウンロードする自動化スクリプトです。 |

### 2. ソースコード本体 (`pyjpboatrace/` フォルダ)
ここがプログラムの実体です。

#### メイン機能
| ファイル名 | 役割 |
| :--- | :--- |
| `pyjpboatrace.py` | **司令塔**。ユーザーは基本的にこのクラスを使います。他の部品を統括します。 |
| `user_information.py` | **会員証**。ユーザーIDやパスワードなどの個人情報を安全に保持します。 |
| `drivers.py` | **手足**。ChromeやFirefoxなどのブラウザを起動・操作する機能です。 |

#### 情報収集 (`scraper/` フォルダ)
Webサイトから情報を取ってくる「調査員」たちです。
| ファイル名 | 役割 |
| :--- | :--- |
| `stadiums_scraper.py` | 「今日はどこの会場でレースがある？」を調べます。 |
| `races_scraper.py` | 「その会場ではどんなレースが行われる？」を調べます。 |
| `race_info_scraper.py` | 「選手は誰？モーターの調子は？」といった詳細情報を調べます。 |
| `odds_...scraper.py` | 各種オッズ（配当）情報を調べます。オッズの種類ごとにファイルが分かれています。 |
| `result_scraper.py` | レースの結果と、いくら払い戻されるかを調べます。 |

#### 投票操作 (`operator/` フォルダ)
実際にお金を動かす「会計係」たちです。
| ファイル名 | 役割 |
| :--- | :--- |
| `depositor.py` | 銀行口座からボートレースの口座へ入金します。 |
| `better.py` | 実際に舟券を購入（投票）します。 |
| `withdrawer.py` | 勝利金を銀行口座へ出金します。 |
| `betting_limit_checker.py` | 「今いくら使える？」を確認します。 |

#### その他 (`utils/` など)
| ファイル名 | 役割 |
| :--- | :--- |
| `certification.py` | ログイン処理を行います。サイトに入るための鍵を開ける係です。 |
| `validator.py` | 「日付が間違っていないか？」などの入力チェックを行います。 |
