# 02｜システム全体図：ブラウザ・Python・データベースの関係

## まず全体を眺める

~~~mermaid
flowchart TD
  U[鑑賞者のブラウザ]
  UI[HTML・CSS・JavaScript]
  API[Python FastAPI / Vercel]
  SQL[(Supabase PostgreSQL)]
  FILE[50作品の画像・一覧CSV]
  GH[GitHub ソースコード]
  U --> UI
  UI -->|GET 作品一覧・集計| API
  UI -->|POST 点数・比較投票| API
  API -->|秘密鍵で REST API| SQL
  API -->|作品情報を読む| FILE
  UI -->|画像を取得| FILE
  GH -.->|将来の自動デプロイ設定| API
~~~

上の矢印は「情報が移動する方向」を表しています。

## ブラウザ側＝フロントエンド
**フロントエンド**とは、鑑賞者に見える画面と、画面上の操作を担当する部分です。

- `public/index.html`：採点スライダーや画像の置き場所を記述
- `public/styles.css`：位置、文字、余白、画面幅に応じた見た目
- `public/app.js`：画像表示、左右移動、採点ボタン、API通信、グラフを生成

ブラウザは自分の回答と匿名IDを `localStorage` に保存します。これは「その端末・そのブラウザ内の小さな保存領域」です。他の端末へ自動同期されません。

## サーバー側＝バックエンド
**バックエンド**は、誰かに見せる画面ではなく、データの受け渡しと保存を担当します。

- `app.py`：FastAPIで `/api/...` の窓口を作る
- `requirements.txt`：FastAPI、Uvicorn、httpx をインストール
- `sample_manifest.csv`：50作品の情報の元データ
- `supabase/schema.sql`：保存先の表と集計関数の定義

### データ保存ルート：公開サイトとMacで違う
- **公開サイト**：Python → Supabase のPostgreSQL（永続的な共通DB）
- **Macのローカル実行**：`SUPABASE_URL` と `SUPABASE_SECRET_KEY` の指定がなければSQLite（`data/ratings.sqlite3`）
- **Vercelで秘密鍵が未設定**：SQLiteに切り替えず `503` で保存を停止

※ ローカルでも両方の環境変数を設定するとSupabaseを使います。テスト時は本番データに混ぜないよう注意してください。

## 1. 作品一覧を表示する通信

~~~text
① 鑑賞者がページを開く
② app.js → GET /api/artworks
③ app.pyがsample_manifest.csvから読んだ50作品をJSONで返す
④ app.jsが作品01の画像URLを<img>に入れる
⑤ ブラウザが画像データを取得し、画面に表示する
~~~

**JSON** は次のような形式です。

~~~json
[
  {
    "id": "ART-001",
    "title": "光を見上げる人物",
    "genre": "人物",
    "image_url": "/images/art_001.jpg"
  }
]
~~~

※ これは**GitHubのコードが返すローカル／通常配置の例**です。2026-11-23のVercelへの直接デプロイ版では、画像URLだけをGitHubの公開画像URLに差し替えています。両者は完全には同じコードではありません。詳しくは[デプロイ手順](06_SETUP_DEPLOY.md)に記載。

## 2. 採点を保存する通信

~~~text
鑑賞者が72点を選ぶ
        ↓
app.js : fetch('/api/ratings', {method: 'POST', ...})
        ↓ JSON
app.py : Ratingモデルで入力確認
        ↓
Supabase REST API : ratingsテーブルに1行 INSERT
        ↓
サーバーが { "saved": true } と返す
        ↓
app.js : 自分のブラウザにも回答を記録し、次の作品を表示
~~~

「保存成功」の返答があったときだけ、JavaScriptは自分の回答を確定します。

## 3. 集計を表示する通信
~~~text
鑑賞者が「結果」を押す
    ↓
app.js : GET /api/stats
    ↓
app.py : SupabaseのRPC art_rating_summary() を呼ぶ
    ↓
Supabase : SQLで平均・分布などを計算
    ↓
JSONの集計結果をapp.jsへ返す
    ↓
JavaScriptが数値と横棒グラフを画面に表示
~~~

個々の参加者のUUIDや採点行を、一般公開の `/api/stats` レスポンスに含めません。ただし **API自体へのレート制限は未実装** です。

## 4. GitHubとVercelは同じサービスではない
- GitHub：コードの保存と変更履歴
- Vercel：Webアプリを実行
- Supabase：評価データを蓄積

**このプロジェクトの初回公開はVercelへの直接デプロイ**。2026-11-23時点では、GitHubに変更を保存するだけで本番に自動反映される設定はありません。Git連携は別途構成する必要があります。

## 5. 「秘密鍵」が使われる場所

~~~text
よい流れ：
ブラウザ → PythonのAPI → Vercel環境変数の秘密鍵 → Supabase

危険な流れ：
ブラウザのapp.jsへ秘密鍵を直接書く → 誰でも秘密鍵を取得できる
~~~

公開サイトのコードは誰にでも見られます。秘密鍵、トークン、実際の `.env` ファイルをGitHubへ置いてはいけません。

## 6. プログラムの処理とデータの保存を分ける理由
ブラウザを閉じても、別の人が来ても、評価データを同じ場所へ蓄積するためです。VercelのPython関数が動くマシンの一時ファイルに保存すると、起動し直したときデータが失われる可能性があります。そこで公開環境ではSupabaseを使います。
