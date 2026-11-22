# 05｜データベース完全解説：SupabaseとSQLを初歩から

参照：[supabase/schema.sql](../supabase/schema.sql)／[app.py](../app.py)。

## 1. データベースとは「検索できる表の集まり」
Excelを想像してください。Excelなら1つのファイルに表を置きます。データベースでは、多数の人が同時に評価を送っても安全に記録・検索・集計できるように設計します。

このアプリは **PostgreSQL** という種類のデータベースを、**Supabase** 上で使っています。
ローカルでは簡単な **SQLite** を利用します。

### 覚える言葉
- **テーブル**：行と列を持つ表。
- **カラム**：列の項目名。
- **レコード／行**：1件の記録。
- **主キー（PRIMARY KEY）**：重複しない行を識別する組。
- **外部キー（REFERENCES）**：別テーブルに実在するIDだけを認める。
- **制約（CHECK）**：「0～100点」などのルールをDB自身が守る。
- **SQL**：DBに「追加して」「探して」「平均して」と頼む言語。

## 2. テーブルは3つ

| テーブル | 何を保存する？ | 例 |
|---|---|---|
| `artworks` | 作品の基本情報 | ID、タイトル、ジャンル |
| `ratings` | 1人が1作品に付けた点数 | 作品ID、参加者ID、72点、理由、時間、再評価 |
| `pair_votes` | 2作品の比較結果 | 参加者ID、左右の作品ID、選ばれた作品ID |

### 作品の行
~~~text
artworks
id        | title            | genre
ART-001   | 光を見上げる人物 | 人物
ART-002   | 赤いポピー       | その他
~~~

### 採点の行
~~~text
ratings
artwork_id | participant_id          | score | reason | duration_seconds
ART-001    | 例のUUID                 | 72    | 構図   | 12.0
~~~

## 3. SQLを1文ずつ見る
~~~sql
create table if not exists public.artworks (
  id text primary key,
  title text not null,
  genre text not null
);
~~~

- `create table`：テーブルを作る。
- `if not exists`：まだ存在しない場合だけ作る。
- `public.artworks`：`public` というスキーマ内の `artworks` テーブル。
- `text`：文字列。
- `primary key`：IDの重複を禁止。
- `not null`：未入力を禁止。

### 0～100点しか登録できない
~~~sql
score integer not null check (score between 0 and 100)
~~~
Pythonでも範囲を確認しますが、DB自身も範囲を守る設計です。二重にチェックすると、予期しない入力からデータを守りやすくなります。

### 同じ人が同じ作品へ2回登録しない
~~~sql
primary key (artwork_id, participant_id)
~~~
2つの列を「セットで重複禁止」にしています。ただし、`participant_id` を別のUUIDに変えれば別人として扱われるため、**本人の一意性は保証しません**。

## 4. なぜ作品と評価を別の表にする？
1つの作品が100人に評価された場合、作品タイトルを100回保存する必要はありません。`ratings` には作品IDだけを保存し、`artworks` のタイトルに結びつけます。
これが「重複する情報を減らす設計」の考え方です。

## 5. 代表的なSQL
### 作品を一覧で見る
~~~sql
select id, title, genre
from public.artworks
order by id;
~~~
`select` は列の取得。`from` は対象テーブル。`order by` は並べ替え。

### 平均点を計算する
~~~sql
select artwork_id, count(*) as 件数, avg(score) as 平均点
from public.ratings
group by artwork_id
order by artwork_id;
~~~
- `count(*)`：行数。
- `avg(score)`：点数の平均。
- `group by artwork_id`：作品IDごとに分けて集計。

※ 運用DBに対するこのSQLの実行結果を、参加者の個票として一般公開する設計ではありません。

## 6. アプリの集計用RPC
公開サイトの `GET /api/stats` は、PythonからSupabaseの `art_rating_summary()` を呼びます。
この関数は件数・平均点・分布・理由・ジャンル・再評価の平均変化・比較件数を **JSON** にまとめて返します。
`security definer` によって関数に必要な権限を持たせているため、**その関数を実行できるロールの制限が重要**です。

ソースの `schema.sql` と、現在の運用DBに適用した集計関数は、`search_path` の指定などの実装差があります。どちらでも安易に公開ロールへ `EXECUTE` 権限を追加しないでください。正式に改善する際はSQL変更をマイグレーションとして管理し、運用DBとGitHubを一致させましょう。

## 7. RLS（Row Level Security）とアクセス権
**RLS** とは「どの行を誰が操作できるか」を制御するPostgreSQLの仕組み。

このアプリでは：
~~~sql
alter table public.ratings enable row level security;
revoke all on public.ratings from anon, authenticated;
~~~
ブラウザがSupabaseへ直接書き込むのではなく、Pythonのサーバーを経由します。
Vercelにある秘密鍵は強い権限を持つため、`anon` や `authenticated` が拒否されていても、**Pythonの公開APIが無制限なら誰でもそのAPIへ送信できる**点に注意してください。

現状は追加の本人認証・レート制限・Bot対策がありません。公開研究の長期運用前に対策が必要です。

## 8. Supabaseの秘密鍵を扱う
環境変数：
- `SUPABASE_URL`：APIの住所。
- `SUPABASE_SECRET_KEY`：強い権限の秘密鍵。秘密にする。

**絶対にしないこと：**
- `public/app.js` に秘密鍵を書く
- GitHubのREADMEやIssueに鍵を貼る
- `.env` をリポジトリにコミットする
- 画面共有で鍵の中身を表示する

Secret keyはVercelのプロジェクト設定で安全に登録します。アプリのソースコードには、設定名だけを書きます。

## 9. どの値が集計される？
- `score` は最初の評価だけが平均点・分布の対象。
- `revised_score - score` が再評価の差分。
- `reason` は1件あたり1種類（現状は複数選択不可）。
- `duration_seconds` はブラウザの計測値であり、操作環境の影響を受ける。
- `pair_votes` は比較件数を蓄積するが、現行の結果画面は作品ごとの比較勝率を表示しない。

## 10. 初心者向けのSQL練習
本番DBのデータを消さないよう、まずは**ローカル環境か専用の練習プロジェクト**を使ってください。

1. `select id, title from public.artworks limit 3;`
2. `select count(*) from public.ratings;`
3. `select avg(score) from public.ratings;`
4. `select reason, count(*) from public.ratings group by reason;`

削除命令の `DELETE`、`DROP`、全体の `UPDATE` は、意味を理解するまで本番で実行しないでください。
