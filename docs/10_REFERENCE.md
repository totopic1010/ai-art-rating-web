# 10｜仕様・用語・API早見表

「どのファイルに何がある？」をすぐ確認したいときの索引です。

## 1. ファイル対応表

| ファイル | 役割 | 主な名前 |
|---|---|---|
| `public/index.html` | 画面の構造 | `artImage`、`score`、`revealDialog` |
| `public/styles.css` | 白黒の見た目・レイアウト | `.gallery-view`、`.art-frame` |
| `public/app.js` | 画面の振る舞い・通信 | `init`、`renderArtwork`、`saveRating`、`renderSummary` |
| `app.py` | PythonのAPIと保存ロジック | `Rating`、`add_rating`、`stats` |
| `sample_manifest.csv` | 50作品の台帳 | `id,file,genre,title,source,row,column` |
| `public/images/` | JPEG50枚 | `art_001.jpg` ～ `art_050.jpg` |
| `supabase/schema.sql` | DBのテーブルと集計関数 | `artworks`、`ratings`、`pair_votes` |
| `tests/test_app.py` | ローカルAPIテスト | `test_app_flow`、`test_hosted_requires_database` |
| `requirements.txt` | Pythonの追加ライブラリ | fastapi、uvicorn、httpx |
| `README.md` | プロジェクトの入口 | 教材の目次・起動方法 |

## 2. APIルート

| メソッド | パス | 役割 | 典型的な成功応答 |
|---|---|---|---|
| GET | `/api/health` | 簡易健康確認 | 200 |
| GET | `/api/artworks` | 作品一覧50件 | 200 |
| POST | `/api/ratings` | 評価1件を保存 | 201 |
| POST | `/api/pair` | 比較投票1件を保存 | 201 |
| GET | `/api/stats` | 件数・平均などを集計 | 200 |
| GET | `/` | 鑑賞画面（ローカル／公開） | 200またはリダイレクト |

`health` は設定・起動の簡易チェック。DBの実接続は `stats` などでも確認してください。

## 3. 採点リクエスト例
以下は **JSONの説明例** です。公開DBにそのまま送信するための指示ではありません。

~~~json
{
  "artwork_id": "ART-001",
  "participant_id": "8cf5caa1-c44a-4e6f-9c2a-513c1f914a00",
  "score": 72,
  "reason": "構図",
  "duration_seconds": 12.3,
  "revised_score": 65,
  "info_shown": true
}
~~~

### どこで使われる？
- `public/app.js`：`saveRating()` が上のJSONを組み立てる。
- `app.py`：`Rating` が型・範囲を検証。
- Supabase：`ratings` テーブルに保存。
- `GET /api/stats`：保存データの平均などを返す。

## 4. 集計JSONの例（説明用、実際の値ではない）
~~~json
{
  "count": 3,
  "average": 73.3,
  "artworks": [
    {"id": "ART-001", "count": 2, "average": 70.0}
  ],
  "genres": [],
  "distribution": {"0": 0, "20": 0, "40": 1, "60": 1, "80": 1},
  "reasons": {"構図": 1},
  "avg_duration": 12.5,
  "avg_shift": -7.0,
  "shift_count": 1,
  "pair_count": 2
}
~~~

## 5. HTTPエラーの早見表
- `200 OK`：取得成功。
- `201 Created`：登録成功。
- `400 Bad Request`：作品IDなどが不正。
- `404 Not Found`：ページ・ファイルが見つからない。
- `409 Conflict`：DBの重複制約に抵触。
- `422 Unprocessable Entity`：入力モデルの条件に合わない。
- `500 Internal Server Error`：サーバー内部で例外が発生。
- `502 Bad Gateway`：Supabaseとの通信や上流の処理に失敗。
- `503 Service Unavailable`：公開環境のDB設定がない。

## 6. よく出るコード用語

| 用語 | 一言で |
|---|---|
| `variable` / 変数 | データを入れる名前 |
| `function` / 関数 | まとまった処理 |
| `return` | 処理の答えを返す |
| `if` | もし〜なら |
| `for` | 1件ずつ繰り返す |
| `list / array` | 複数データの並び |
| `dict / object` | 名前と値のセット |
| `JSON` | 通信でよく使うデータ形式 |
| `UUID` | ランダムな識別子 |
| `async / await` | 通信などの完了を待つ書き方 |
| `fetch` | ブラウザからAPIを呼ぶ関数 |
| `FastAPI` | PythonでAPIを作る仕組み |
| `Pydantic` | 入力データの型・範囲を検証する仕組み |
| `SQL` | DBを操作する言語 |
| `RPC` | ネットワーク経由でサーバーの関数を呼ぶ |
| `RLS` | DBの行ごとのアクセス制御 |
| `environment variable` / 環境変数 | プログラムの外に置く設定 |
| `localStorage` | ブラウザ内の保存場所 |
| `SQLite` | ファイル型の小さなDB |
| `PostgreSQL` | 多数のデータを扱えるDB |
| `Git commit` | 変更履歴の記録 |
| `deploy` | 公開環境へ配置 |

## 7. 次に読む場所
- 文法を学ぶ → [03 Python](03_PYTHON_GUIDE.md) / [04 Frontend](04_FRONTEND_GUIDE.md)
- 全体像を知る → [02 アーキテクチャ](02_ARCHITECTURE.md)
- 手順を再現する → [06 セットアップ・デプロイ](06_SETUP_DEPLOY.md)
- 安全性を考える → [08 セキュリティ・研究](08_SECURITY_RESEARCH.md)

---
**この資料は教育・再現を目的とした技術解説であり、現行プロトタイプが研究倫理審査やセキュリティ監査を通過したことを示すものではありません。**
