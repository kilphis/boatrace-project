# pyjpboatrace Manifesto

## 📂 ディレクトリ構成図

`pyjpboatrace` の全体像は以下のようになっています。

```text
pyjpboatrace/
├── README.md                   # 説明書 (使い方やインストール方法)
├── pyproject.toml              # プロジェクト設定 (依存ライブラリなど)
├── LICENSE                     # ライセンス表記
├── .gitignore                  # Gitで無視するファイルの設定
├── download_html_for_test.sh   # テスト用HTMLデータのダウンロードスクリプト
├── update_readme.py            # READMEの更新用スクリプト
├── pyjpboatrace/               # 【ソースコードの本体】
│   ├── __init__.py             # パッケージ初期化ファイル
│   ├── pyjpboatrace.py         # 司令塔クラス (ユーザーが直接使うメインファイル)
│   ├── user_information.py     # ユーザー情報 (ID/Pass) を管理するクラス
│   ├── drivers.py              # ブラウザ操作 (Chrome/Firefox等) を管理するモジュール
│   ├── certification.py        # ログイン認証処理を行うモジュール
│   ├── validator.py            # 入力データの妥当性チェックを行うモジュール
│   ├── exceptions.py           # エラー定義 (独自のエラーメッセージなど)
│   ├── const.py                # 定数定義 (変更しない値)
│   ├── scraper/                # 【情報収集部門】 (Webサイトからデータを取る)
│   │   ├── base.py                 # スクレイピングの基本クラス
│   │   ├── stadiums_scraper.py     # 開催場一覧を取得
│   │   ├── races_scraper.py        # 12レース一覧を取得
│   │   ├── race_info_scraper.py    # レース基本情報 (選手・モーターなど) を取得
│   │   ├── result_scraper.py       # レース結果・払い戻しを取得
│   │   ├── win_placeshow_odds_scraper.py  # 単勝・複勝オッズを取得
│   │   ├── ... (他のオッズ取得ファイル)
│   │   └── _parser/                # HTML解析の下請け処理
│   ├── operator/               # 【投票操作部門】 (お金を扱う・投票する)
│   │   ├── base.py                 # 操作の基本クラス
│   │   ├── better.py               # 投票を実行するクラス
│   │   ├── depositor.py            # 入金を実行するクラス
│   │   ├── withdrawer.py           # 出金を実行するクラス
│   │   ├── betting_limit_checker.py# 購入限度額を確認するクラス
│   │   └── static.py               # 静的な操作ヘルパー
│   └── utils/                  # 便利ツール置き場
│       └── str2num.py              # 文字列を数値に変換するツール
└── tests/                      # 【品質保証部門】 (プログラムのテスト)
    ├── test_pyjpboatrace.py    # メイン機能のテスト
    ├── data/                   # テスト用データ
    └── ... (各機能のテストファイル)
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
