# AI Art Rating — Web Edition v6
**はじめてプログラミングを学ぶ人のための、AIアート鑑賞・採点アプリと日本語教科書**

> 50枚のAI生成画像を鑑賞し、0～100点で評価・比較・集計するWebアプリ。手描きのスケッチに基づく、余白の大きい白黒のUIを採用しています。

- **Webアプリを体験**：https://ai-art-rating-web.vercel.app/
- **ソースコード全体**：このGitHubリポジトリの `app.py`、`public/`、`supabase/`、`tests/`
- **初心者におすすめの入口**：[まずはここから](docs/00_START_HERE.md)
- **学習目標**：「この1行が何をしているか」を説明でき、自分の手で1つ改良すること。

## できること
- 50作品を左右に移動して鑑賞（`01 / 50` と進行目盛り）
- 0～100点の採点と、任意の評価理由
- AI制作に関する説明を読んだ後の任意の再評価
- 判断にかかった時間の記録
- 2作品の比較投票
- 平均点・ジャンル別傾向・評価分布などの表示
- 自分のブラウザに残る回答のCSVダウンロード

**未実装**：画像のアップロード／アプリ内での画像生成／参加者の厳密な本人確認／研究用の同意・条件割当／Bot対策・レート制限。厳密な研究実験や大規模な公開利用向けに完成しているわけではありません。

## 📖 初心者向け・公開教科書（全11章）

| 順序 | 教材 | 何が分かるか |
|---|---|---|
| 0 | [はじめての人へ](docs/00_START_HERE.md) | 技術用語が分からなくても読める入口 |
| 1 | [要件定義書](docs/01_REQUIREMENTS.md) | 何を実装し、何が未実装なのか |
| 2 | [システム全体図](docs/02_ARCHITECTURE.md) | ブラウザ→Python→Supabaseの流れ |
| 3 | [Python完全解説](docs/03_PYTHON_GUIDE.md) | `app.py` の関数を1つずつ理解 |
| 4 | [HTML/CSS/JavaScript解説](docs/04_FRONTEND_GUIDE.md) | 手描きUIが動く画面になるまで |
| 5 | [SQL・データベース解説](docs/05_DATABASE.md) | 評価がどのように蓄積・集計されるか |
| 6 | [Mac起動・デプロイ手順書](docs/06_SETUP_DEPLOY.md) | ダウンロードからWeb公開まで |
| 7 | [エラー対処辞典](docs/07_TROUBLESHOOTING.md) | 404・409・422・500・502・503の直し方 |
| 8 | [セキュリティと研究倫理](docs/08_SECURITY_RESEARCH.md) | 匿名IDの限界と卒論前に必要な改善 |
| 9 | [14日間の学習ロードマップ](docs/09_LEARNING_PLAN.md) | 1日ごとの演習で理解する |
| 10 | [API・用語・ファイル早見表](docs/10_REFERENCE.md) | 忘れたことを検索して確認 |
| 補足 | [公開状態と開発記録](docs/11_DEPLOYMENT_STATUS.md) | 本番サイトとGitHubの違い・検証状況 |

### 学び方
**最初は0章 → 2章 → 4章 → 3章の順番**がおすすめ。画面を見ながら「それを動かすコードはどこか？」を調べると理解しやすくなります。学習記録は [LEARNING_CHECKLIST.md](LEARNING_CHECKLIST.md) も使えます。

## ファイル構成
~~~text
ai-art-rating-web/
├── app.py                   # Python / FastAPI
├── requirements.txt         # Pythonの追加パッケージ
├── sample_manifest.csv      # 50作品の一覧
├── public/
│   ├── index.html           # HTML
│   ├── styles.css           # CSS
│   ├── app.js               # JavaScript
│   └── images/              # 作品JPEG 50枚
├── supabase/
│   └── schema.sql           # Supabase用SQL
├── tests/
│   └── test_app.py          # APIのテスト
├── docs/                    # 日本語の完全解説書
├── .env.example             # 秘密情報を含まない設定例
├── .python-version          # 推奨Pythonバージョン
└── .gitignore               # 登録しないファイルを指定
~~~

## まずMacで動かしてみる
Macのターミナルで `app.py` のあるフォルダに移動して実行：

~~~bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload
~~~

Safariで http://127.0.0.1:8000/ を開きます。初期状態ではSQLiteにローカル保存します。コマンドの意味やPython 3.12の推奨理由は[手順書](docs/06_SETUP_DEPLOY.md)で解説しています。

## Web公開の構成
- **GitHub**：ソースを公開して履歴を残す
- **Vercel**：Python APIとWeb画面を公開
- **Supabase**：共通の評価データを保存
- **ブラウザのlocalStorage**：自分の匿名IDと回答を保存

**重要：2026-11-23時点の本番版はVercelへの直接デプロイです。GitHubへコミットしても自動で本番に反映される設定は未完了です。** 詳細は[公開状態](docs/11_DEPLOYMENT_STATUS.md)。

## データ・安全・研究について
- 作品50枚は**1枚のAI生成コンタクトシートから切り出した試験用素材**。卒論の本実験に使うには刺激選定から再検討が必要です。
- ブラウザのUUIDは本人認証ではありません。
- **秘密鍵をGitHub、ブラウザのJavaScript、チャット、スクリーンショットへ貼らないこと。**
- 現行の公開APIにはレート制限や研究参加への同意機能がありません。大規模利用・研究収集前に対策が必要です。
- コードが公開されていることと、自由に再利用できるライセンスがあることは別です。`LICENSE` は未設定です。

**技術と研究の注意点は [第8章](docs/08_SECURITY_RESEARCH.md) を必ず読んでください。**

---
このREADMEと教科書は、2026年11月23日時点のリポジトリの実装を確認して書いています。Pythonやサービス仕様は今後変わる可能性があります。
