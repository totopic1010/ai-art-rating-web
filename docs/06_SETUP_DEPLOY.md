# 06｜再現手順書：Macの初心者が動かし、GitHub・Supabase・Vercelへ公開する

この手順は**自分用に再現する**ためのものです。何も知らない人でも操作できるよう、コマンドの意味も説明します。
当初の作成日：2026年11月23日。各サービスの画面名は変更される場合があります。

## 全体像：4段階
1. Macでコードを入手する。
2. Macだけで動かす（SQLite保存）。
3. Supabaseに本番用の保存先を作る。
4. GitHubにコードを保存し、Vercelに配置する。

この順番なら「どの段階で止まったか」が分かります。

## 準備するもの
- MacとSafariなどのブラウザ。
- Python 3.12を推奨。`python3 --version` で確認。
- ターミナル（Macでコマンドを入力するアプリ）。
- GitHubアカウント（オンラインでコードを管理する場合）。
- SupabaseとVercelのアカウント（Web公開する場合）。
- インターネット接続。

**お金について**：小規模で無料枠から始められることがありますが、作成時に契約プランや機能ごとの料金を自分で確認してください。無料枠の制限に達すると停止・制限が発生する場合があります。プラン変更を無断で行わないこと。

## STEP 1｜ソースコードをMacへ取得
GitHub：[ai-art-rating-web](https://github.com/totopic1010/ai-art-rating-web)

初めてならGitHubの緑色の **Code** ボタン→ **Download ZIP** →ダウンロードしたZIPをダブルクリックして解凍。

フォルダの中を確認：
~~~text
ai-art-rating-web/
├── app.py
├── requirements.txt
├── sample_manifest.csv
├── public/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── images/    ← art_001.jpg ～ art_050.jpg
├── supabase/
│   └── schema.sql
├── tests/
│   └── test_app.py
└── docs/
~~~

ZIPの外側の親フォルダではなく、`app.py` があるフォルダが作業場所です。

## STEP 2｜ターミナルを開いてフォルダへ移動
Macで **⌘＋スペース** →「ターミナル」と入力して起動。

以下のように入力：
~~~bash
cd 
~~~
`cd` の後に**半角スペース**を入れて、Finderから `app.py` があるフォルダをターミナルへドラッグすると、そのフォルダの場所が自動で入力されます。最後にEnter。

~~~bash
pwd
ls
~~~
- `pwd`：「今いるフォルダ」を確認。
- `ls`：そのフォルダのファイル一覧を見る。
- 一覧に `app.py` と `public` が見えればOK。

## STEP 3｜仮想環境を作る
~~~bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
~~~
- `python3 --version`：Pythonのバージョンを調べる。
- `python3 -m venv .venv`：アプリ用の独立したPython環境を作る。
- `source .venv/bin/activate`：その環境を使う。
- ターミナルの先頭に `(.venv)` が表示されることがあります。

Python 3.14などで追加ライブラリのインストールが失敗したら、3.12をインストールしてから `python3.12 -m venv .venv` で作り直します。元の`.venv`は必要に応じて削除し、作り直してください。

### なぜ仮想環境が必要？
Aというアプリは古いライブラリ、Bというアプリは新しいライブラリが必要、ということがあります。`.venv` を分ければ、それぞれの依存関係が衝突しにくくなります。

## STEP 4｜必要な部品をインストール
~~~bash
python -m pip install -r requirements.txt
~~~
- `pip` はPythonの追加パッケージをインストールする道具。
- `-r requirements.txt` は「必要なものの一覧を読み込んで」という意味。

今回の主な部品：
- `fastapi`：Web APIを作る。
- `uvicorn`：MacでPythonのWebサーバーを起動する。
- `httpx`：Supabaseへの通信に使う。

## STEP 5｜MacでWebアプリを動かす
~~~bash
python -m uvicorn app:app --reload
~~~
意味：
- `python -m uvicorn`：Uvicornを実行。
- `app:app`：左は `app.py`、右はその中の `app = FastAPI(...)`。
- `--reload`：コードの保存時に自動的にサーバーを再起動する（開発用）。

Safariで次を開く：
- http://127.0.0.1:8000/
- http://127.0.0.1:8000/api/health

`127.0.0.1` は「自分のパソコン自身」という意味。インターネットへの公開はまだしていません。

環境変数が未設定なら健康確認の `mode` は `local`。採点したデータは原則として `data/ratings.sqlite3` に保存されます。

**終了方法**：ターミナルで `Control + C`。

## STEP 6｜テストを動かす
~~~bash
python -m pip install pytest
python -m pytest -q
~~~
`tests/test_app.py` がAPIを自動で確認します。現在のテストは、ローカルSQLiteでの保存、重複拒否、不正点数、集計、比較投票、公開環境でのDB未設定時の挙動を扱います。

**テストに合格した＝本番サイトが完全に正常** ではありません。本番のネットワーク、権限、ブラウザ操作は別途検証する必要があります。

## STEP 7｜Supabaseにデータベースを作る
1. https://supabase.com/ にログイン。
2. 新しいプロジェクトを作成。プランと費用を確認する。
3. 地域（例：Tokyo）を選ぶ。
4. Project画面の **SQL Editor** を開く。
5. GitHubの `supabase/schema.sql` を開いて全体をコピー。
6. SQL Editorに貼り付けて実行する。
7. **Table Editor** に `artworks`、`ratings`、`pair_votes` があるか確認。
8. `artworks` に50行があるか確認。

`schema.sql` は現行の初期セットアップ用ですが、すでに稼働しているDBに何度も変更を適用する場合は注意が必要です。本番のDB設計とGitHubのSQLに一部差分があり、将来的にマイグレーションとして整備する予定です。

**絶対にしない**：知らないSQLを本番で実行しない、`DELETE FROM ratings` や `DROP TABLE` を試さない。

## STEP 8｜SupabaseのURLと秘密鍵をVercelへ登録
Supabaseの管理画面で：
- Project URL（`https://...supabase.co` の形式）を確認。
- **Project Settings → API Keys** のSecret key（`sb_secret_` から始まるもの）を確認。

Vercelの**自分の**プロジェクトで **Settings → Environment Variables** を開き、以下を設定します。

| Name | Value | 公開してよい？ |
|---|---|---|
| `SUPABASE_URL` | Project URL | URL自体は一般に公開可能だがコードへ固定せず環境変数推奨 |
| `SUPABASE_SECRET_KEY` | Secret key | **絶対に公開しない** |

- 本番なら **Production** を対象に設定。
- Preview環境でもSupabaseを使うなら、適切な接続先・鍵を **Preview** に別途設定。**現行の実プロジェクトでは秘密鍵はProductionのみ**に存在しました（2026-11-23時点）。
- 変数を追加・変更したら **新しいデプロイ** が必要です。
- 値をGitHub、README、チャット、画面写真へ貼らないでください。

## STEP 9｜GitHubで自分のコードを管理する
### A. 初心者：Web画面でアップロード
1. https://github.com/new からリポジトリを作る。
2. 初回はPrivateでもよい。一般公開したい場合のみPublicを選ぶ。
3. **uploading an existing file** から、`app.py` のあるフォルダの**中身を**登録する。
4. `public` 内のHTML/CSS/JavaScriptと画像50枚を含める。
5. `Commit changes` を押す。
6. リポジトリ直下に `app.py` があることを確認。

**GitHubにアップロードしないもの**：実際の`.env`、`.venv`、`data/ratings.sqlite3`、認証トークン、秘密鍵。

### B. 少し慣れたらターミナルでGit
~~~bash
git init
git add .
git commit -m "Initial AI Art Rating"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-art-rating-web.git
git push -u origin main
~~~
`YOUR_USERNAME` は自分のGitHub名へ。すでにGit管理されているフォルダでは `git init` や `remote add` が不要の場合があります。`git status` で現状を確認してください。

- `git add .`：変更を登録する準備。
- `git commit -m`：変更履歴を記録。
- `git push`：GitHubへ送信。

## STEP 10｜VercelでWeb公開
1. https://vercel.com/ にログイン。
2. **Add New → Project** などから新規プロジェクト作成。
3. GitHubリポジトリをImportし、`app.py` のあるルートをRoot Directoryに指定。
4. Framework Preset を **FastAPI** に設定（自動判定されない場合）。
5. `SUPABASE_URL` と `SUPABASE_SECRET_KEY` をProduction環境へ登録。
6. **Deploy** を実行。
7. 発行された`.vercel.app` URLを開く。

### すでに存在するVercelプロジェクトを使う場合
新しいプロジェクトを重複して作らず、既存のプロジェクトの **Settings → Git** などにGitHub連携の設定があるか確認します。画面表示は変更される場合があります。

### このプロジェクト固有の注意
2026-11-23に公開した `ai-art-rating-web` は、最初のデプロイでGitHub APIのアクセス制限に遭い、**Vercelへファイルを直接アップロードして公開**しています。
したがって現時点で**GitHubを更新するだけで本番が自動更新されるとは限りません**。

さらに、Vercel直接配置版では画像のURLをGitHubの公開画像に向ける一時的な差し替えを行いました。リポジトリの `app.py` は `/images/...` のURLを返します。GitHub連携デプロイへ移行する際は、画像表示を含めて改めて確認してください。

## STEP 11｜公開後の検証
公開URLを `https://あなたのサイト.vercel.app` とする場合：

1. `/` を開く → 鑑賞画面が表示される。
2. `/api/health` を開く → `ok:true`、`artworks:50`、`mode:supabase` を確認。
3. `/api/artworks` を開く → 作品情報が50件返る。
4. `/api/stats` を開く → JSONが返る。これはDB接続の確認にもなる。
5. 画像1枚、前後移動、スライダーの表示を確認。
6. **許可されたテスト用の回答** を保存し、件数が増えることを確認。
7. SupabaseのTable Editorで`ratings`に反映されることを確認。
8. 同じブラウザの同作品で「評価済み」になることを確認。

`/api/health` の `mode:supabase` は**設定があることの表示**で、DB接続成功を保証しません。`/api/stats` の結果や保存テストで確認します。

本番の研究データにテスト回答を混入させたくない場合は、**開発用の別プロジェクト／別DB** で検証してください。

## STEP 12｜変更して再公開
たとえば作品のサイズを変えたい場合：
1. `public/styles.css` を開く。
2. `.art-frame img` の高さなどを変更。
3. Macのローカルサイトで確認。
4. テストを実行。
5. GitHubへコミットしてプッシュ。
6. Git連携が有効ならVercelが再デプロイ。**未連携なら手動で再デプロイ**。
7. 本番サイトで同じ動きを確認する。

**「変更して終わり」ではなく、「変更→テスト→記録→公開→再確認」が開発です。**

## セットアップ参照資料
- FastAPI on Vercel：https://vercel.com/docs/frameworks/backend/fastapi
- Vercel Deployment：https://vercel.com/docs/deployments
- Supabase API Keys：https://supabase.com/docs/guides/api/api-keys
- Supabase RLS：https://supabase.com/docs/guides/database/postgres/row-level-security
- GitHub入門：https://docs.github.com/ja/get-started/start-your-journey/hello-world
