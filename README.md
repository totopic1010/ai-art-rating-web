# AI Art Rating — Web Edition v6

外部で生成したAI画像50枚を鑑賞し、0〜100点で採点・比較・分析するWebアプリ。
手描きのUIを基に、**白背景・黒文字・余白・中央の作品・1/50表示・左の目盛り・下部の評価スライダー**を維持しています。

## できること

- AI画像50枚を表示し、前後移動
- 0〜100点＋評価理由＋判断時間を保存
- 作品のAI制作情報を読んだ後の任意の再評価
- 2作品の比較投票
- 平均点、ジャンル別の傾向、評価分布、理由の集計
- 自分の評価だけCSVに書き出し
- ブラウザごとに匿名のランダム識別子を生成（ログイン不要）

**注意：** 画像は以前制作したテスト用50枚（1枚の画像から切り出したサンプル）。卒論用の実験では、個別生成・条件統制・同意取得などの別準備が必要。画像をサーバーへアップロードする機能は初期版では未搭載。

## 1. Macでローカル起動

Macのターミナルを開き、このフォルダへ移動します。`cd ` と打った後にフォルダをドラッグすれば場所を入力できます。

```bash
cd /path/to/AI_Art_Rating_Deploy
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload
```

ブラウザで `http://127.0.0.1:8000` を開きます。初回にファイル保存先 `data/ratings.sqlite3` が作られます。

**Python 3.14を使っている場合：** 必要パッケージの互換性などに問題が出たら、Python 3.12で仮想環境を作ってください。Vercelの設定は`.python-version`で3.12を指定しています。

## 2. Supabaseを用意

1. https://supabase.com で無料プランのプロジェクトを作成
2. ダッシュボードの **SQL Editor** を開き、`supabase/schema.sql` 全体を貼って実行
3. Project URLを確認
4. **Settings → API Keys** からサーバー向けの **Secret key**（`sb_secret_...`）を確認

**重要：鍵はコード・GitHub・チャットへ貼らない。** `SUPABASE_URL`と`SUPABASE_SECRET_KEY`をVercelの環境変数へ登録する。ブラウザへ公開しない。SQL側では`anon`と`authenticated`の直接アクセスを許可していない。

このアプリはサーバーからSupabase REST APIへアクセスし、個別回答を公開せず集計JSONのみ返します。

## 3. GitHubへ保存

GitHub https://github.com/new で `ai-art-rating-web` という**新しい**リポジトリを作る（既存のPHP掲示板リポジトリは使用しない）。

ローカルでこのフォルダを開いたターミナルで以下を実行：

```bash
git init
git add .
git commit -m "Build AI Art Rating Web MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-art-rating-web.git
git push -u origin main
```

`YOUR_USERNAME`を自身のGitHubユーザー名に置き換えてください。GitHubの認証が必要なら指示に従ってください。

※ 画像50枚を同梱しているのでGitHubのアップロードに数MBかかります。

## 4. Vercelへ公開

1. https://vercel.com/new を開く
2. **Import Git Repository** から `ai-art-rating-web` を選択
3. Python FastAPI アプリが検出されることを確認（ルートの `app.py` に `app = FastAPI(...)` が存在）
4. **Environment Variables** に `SUPABASE_URL` と `SUPABASE_SECRET_KEY` を登録
5. **Deploy** をクリック
6. `https://...vercel.app/` の公開URLを確認
7. `https://...vercel.app/api/health` を開いて、`mode` が `supabase` であることを確認
8. 採点を1件保存し、「結果」に反映されることを確認

**Vercelを先にデプロイしてDBを設定しない場合：** UIは見られても、採点保存は503エラーになります。公開環境はSQLiteの一時保存へ自動フォールバックしません。

**費用：** 個人の小規模テストなら無料プランで開始できる可能性がありますが、枠・利用規約・商用条件はVercelとSupabaseの公式サイトで確認してください。クレジットカード登録や従量課金に注意。

公式情報：
- https://vercel.com/docs/frameworks/backend/fastapi
- https://vercel.com/docs/functions/runtimes/python
- https://supabase.com/docs/guides/api/securing-your-api
- https://supabase.com/docs/guides/getting-started/api-keys

## 5. 学習の順序

1. `public/index.html` で画面の構造（HTML）を理解
2. `public/styles.css` で余白、位置、色を変更
3. `public/app.js` で画像切替・スライダー・API通信を理解
4. `app.py` で `if`、関数、FastAPI、入力検証を学ぶ
5. `supabase/schema.sql` でテーブル、主キー、制約、集計を確認
6. GitHubに変更を記録して、再デプロイ

## 6. 注意と未実装の項目

- ブラウザの匿名IDは削除できるため、不正・重複回答を完全には防げません。実験本番にはログイン、割当トークン、アクセス制限などが必要。
- 公開APIには本番向けのレート制限・Bot対策・管理者機能は未実装。初期は限定公開または小規模テストを推奨。
- 情報提示の前後評価は任意であり、**作者情報の因果効果を検証する統制実験ではありません**。
- 参加同意、研究倫理、提示順序ランダム化、実験条件の割当は卒論本番前に設計してください。
- `get /api/stats` は全体集計のみ公開。匿名ブラウザIDはサーバー上に保存されます。ブラウザのlocalStorageにも自分の回答が残ります。
- 評価理由を増やす際はHTML側の選択肢と`app.py`の許可リストを両方変更します。

## 7. 確認コマンド

```bash
python -m pip install pytest
python -m pytest -q
```

環境変数を追加して実際のSupabaseへのAPI接続も確認してください。今回は外部アカウントの接続情報がないため本番デプロイとSupabase実接続は未実施です。
