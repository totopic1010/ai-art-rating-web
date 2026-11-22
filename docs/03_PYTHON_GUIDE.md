# 03｜Python / FastAPI 完全解説：app.py を上から読めるようになる

参照コード：[app.py](../app.py)。**短い抜粋を説明しています。** 正式な全コードはリンク先を見てください。行番号は変更で動くため、関数名で検索します。

## 0. 学ぶ前に：Pythonがこのアプリで担当すること
Pythonは「採点を受け取る係」です。画面のボタンを直接描いていません。
- JavaScriptからのリクエストを受け取る
- 点数の範囲・作品ID・理由などが正しいか調べる
- データベースへ書く
- 平均点などの集計結果を返す

## 1. 基本の3つの文法
~~~python
score = 72           # 変数：72という値をscoreという名前で持つ
if score >= 60:      # 条件：60点以上なら次の行を実行
    print("高評価")   # 半角スペースで字下げ（インデント）する
~~~

~~~python
def double(n):       # 関数：nを受け取って処理する
    return n * 2     # 呼んだ側に結果を返す

print(double(5))     # 10
~~~

~~~python
artworks = ["作品A", "作品B"]   # 複数の値＝リスト
print(artworks[0])            # 作品A（最初の番号は0）
artwork = {"id": "ART-001", "score": 72}  # 名前と値の組＝辞書
print(artwork["score"])       # 72
~~~

## 2. `import` とは？
冒頭の `import csv`、`import sqlite3`、`import uuid` などは「他のプログラムから便利な道具を借りる」こと。

- `csv`：50作品のCSVを読む。
- `sqlite3`：Macでのローカル保存。
- `uuid`：匿名識別子の型チェック。
- `os`：環境変数を読む。
- `pathlib.Path`：ファイルの置き場所を扱う。
- `httpx`：SupabaseとHTTP通信する。
- `fastapi`：Web APIを簡潔に作る。
- `pydantic`：届いた入力の型や範囲をチェックする。

Python標準搭載のものと、`requirements.txt` で追加インストールするものが混ざっています。

## 3. ファイルの場所と保存方法を決める
~~~python
BASE = Path(__file__).resolve().parent
PUBLIC = BASE / 'public'
DATA = BASE / 'data'
IS_HOSTED = bool(os.getenv('VERCEL'))
SUPABASE_URL = os.getenv('SUPABASE_URL', '').rstrip('/')
SUPABASE_SECRET_KEY = os.getenv('SUPABASE_SECRET_KEY', '')
HAS_SUPABASE = bool(SUPABASE_URL and SUPABASE_SECRET_KEY)
~~~

1行ずつ：
1. `__file__` は今動いているPythonファイル。`BASE` はそのフォルダ。
2. `BASE / 'public'` はその中の `public` フォルダ。
3. `DATA` はローカルDBのファイルを置く場所。
4. `os.getenv('VERCEL')` はVercel環境かを調べる。
5. `SUPABASE_URL` はDBの接続先。
6. `SUPABASE_SECRET_KEY` はDB操作用の秘密鍵。**コードには直接記載しない**。
7. `HAS_SUPABASE` は両方の設定が存在するときだけ `True`。

**補足**：`HAS_SUPABASE=True` は設定があるという意味であり、DBへ実際に通信成功した証明ではありません。

## 4. アプリ本体を作る
~~~python
app = FastAPI(title='AI Art Rating', version='6.0')
~~~
現行コードには追加設定があり、`/docs`、`/redoc`、`/openapi.json` は公開しないようにしています（ドキュメントを無効化するだけでAPIの認証になるわけではありません）。

**FastAPI** は「このURLには、この関数を対応させる」というルールを簡単に書けるライブラリです。

## 5. CSVから作品一覧を作る
~~~python
with (BASE / 'sample_manifest.csv').open(encoding='utf-8-sig', newline='') as f:
    ARTWORKS = [dict(r) for r in csv.DictReader(f)]
ART_IDS = {art['id'] for art in ARTWORKS}
~~~

- `with`：ファイルを開いて、処理が終われば閉じる。
- `as f`：開いたファイルを `f` という名前で扱う。
- `csv.DictReader(f)`：表の1行を辞書にする。
- `[ ... for ... ]`：行の数だけ繰り返し、リストを作る。
- `ART_IDS`：50作品のIDの集合。存在する作品かどうかを高速にチェックするため。

作品数が50になるのは **CSVに50行あるから**で、Pythonが勝手に50作品を作っているわけではありません。

## 6. 届いたデータのルール：`class Rating`
~~~python
class Rating(BaseModel):
    artwork_id: str = Field(max_length=32)
    participant_id: uuid.UUID
    score: int = Field(ge=0, le=100)
    reason: str = Field(default='', max_length=40)
    duration_seconds: float = Field(ge=0, le=3600)
    revised_score: int | None = Field(default=None, ge=0, le=100)
    info_shown: bool = False
~~~

- `class`：関連する設定や処理をまとめる型を作る。
- `str`：文字列。
- `int`：整数。小数点を使わない。
- `float`：小数を含む数。
- `bool`：真偽（TrueまたはFalse）。
- `uuid.UUID`：正しい形式のランダム識別子。
- `ge=0`：0以上。`le=100`：100以下。
- `int | None`：整数または「値なし」。
- `default`：省略されたときの初期値。

例えば `score=105` を送ると入力検証で拒否され、通常 `422` になります。これはUI側だけでなく**サーバー側で守っているルール**です。

## 7. URLと関数を結びつける：API
~~~python
@app.get('/api/health')
def health():
    return {'ok': True, 'artworks': len(ARTWORKS)}
~~~

本物の関数は保存方式の `mode` も返します。`@app.get` は「このURLへのGETが来たら、その直後の関数を呼ぶ」という印です。

- `GET /api/health`：起動の簡易確認
- `GET /api/artworks`：作品一覧を返す
- `POST /api/ratings`：採点を保存
- `POST /api/pair`：比較投票を保存
- `GET /api/stats`：集計を返す

`return` の辞書はFastAPIがJSONに変換してブラウザへ返します。

## 8. 最重要：`add_rating()` を分解する
~~~python
@app.post('/api/ratings', status_code=201)
def add_rating(r: Rating):
    ensure_storage()
    if r.artwork_id not in ART_IDS:
        raise HTTPException(400, '作品IDが不正です。')
    if r.reason not in ('', '色彩', '構図', '独創性', '感情', '技術', 'その他'):
        raise HTTPException(400, '評価理由が不正です。')
~~~

- `POST`：新しいデータを送る方式。
- `status_code=201`：「新規作成成功」を意味するHTTP状態番号。
- `r: Rating`：入力は `Rating` のルールで検証する。
- `ensure_storage()`：公開環境でDB設定がないなら停止する。
- `not in`：許可されている一覧に含まれていない。
- `raise HTTPException(400,...)`：不正な入力だとブラウザにエラーを返す。

次の部分で `values`（保存するデータの辞書）を組み立て、最後に次の分岐をします。

~~~python
if HAS_SUPABASE:
    supabase_request('POST', 'ratings', payload=values)
else:
    # ローカル環境ではsqlite3のINSERTを使用
    ...
~~~

上記の `...` は学習のために省略した部分。**完全な動くコードは必ず [app.py](../app.py) を参照してください**。

### 「保存した」と分かる瞬間
~~~python
return {'saved': True}
~~~
データベースへの処理が終わってからこの結果を返します。JavaScriptはこの返事を確認して、次の画像へ移動します。

## 9. `supabase_request()` の意味
Pythonは `httpx.Client` でSupabaseのREST APIに接続します。

~~~python
headers = {
    'apikey': SUPABASE_SECRET_KEY,
    'Content-Type': 'application/json'
}
~~~

- `headers`：通信に添える情報。
- `apikey`：Supabase側が通信元の権限を判別するための鍵。
- `Content-Type`：「JSONを送ります」という宣言。

**秘匿の原則**：このヘッダーはPythonからSupabaseへ送られます。閲覧者のブラウザに配信するJavaScriptへ書き込まないでください。

エラー時の挙動：
- `409`：作品の重複評価などDBの重複制約違反。
- `502`：DBへの接続または上流APIで失敗。
- `503`：公開環境にDB接続設定がない。
- `422`：Pydanticによる入力チェックで失敗。

## 10. ローカル保存：`local_db()`
~~~python
DATA.mkdir(exist_ok=True)
conn = sqlite3.connect(DATABASE, timeout=10)
~~~

- `mkdir`：フォルダを作る。
- `sqlite3.connect`：ローカルファイルのデータベースを開く。
- `CREATE TABLE IF NOT EXISTS`：初回だけ表を用意する。
- `INSERT INTO ratings`：新しい評価を1件記録する。

**重要**：これはMacのローカル学習用で、Vercel上の一時ファイル保存として使う設計ではありません。

## 11. 集計：`aggregate(rows, pairs)`
ローカル用の集計関数では次のことをしています。
1. 作品IDで点数をグループに分ける。
2. 作品ごとに件数と平均を計算する。
3. ジャンル別も同様に計算する。
4. `0–19`、`20–39`、`40–59`、`60–79`、`80–100` へ得点を分ける。
5. 選ばれた理由を数える。
6. 最初の点数と再評価点数の差を集計する。

例：
~~~python
scores = [50, 80, 90]
average = sum(scores) / len(scores)
print(average)  # 73.333...
~~~
アプリは表示用に小数第1位まで丸めています。

公開環境の `/api/stats` ではPythonが個票を全件取得するのではなく、Supabase側の集計関数 `art_rating_summary()` に依頼します。

## 12. Vercelとローカルで画面の配信が違う
現行コード末尾：

~~~python
if IS_HOSTED:
    @app.get('/')
    def frontend_redirect():
        return RedirectResponse(url='/index.html', status_code=302)
else:
    app.mount('/', StaticFiles(directory=PUBLIC, html=True), name='frontend')
~~~

Vercel上では `public/` の中身を静的ファイルとして直接配信し、Python側ではフォルダをマウントしません。以前はサーバー内部に `public/` フォルダが存在しないため500エラーになりました。ローカルはFastAPIがそのフォルダを配信します。

## 13. 試して学ぶ小課題
1. `GET /api/health` をブラウザで開き、JSONを読む。
2. `app.py` の `Rating.score` を見つけ、何点が許されるか説明。
3. `add_rating()` の全体を読んで「チェック→保存→返信」を線で結ぶ。
4. `aggregate()` の平均計算式を紙に書く。
5. **公開中のDBへ勝手にテスト回答を大量送信しない**。ローカルテストを先に使う。

到達目標：**なぜ「ブラウザで点数を選んだだけ」では保存できず、PythonとDBが必要かを説明できること。**
