# 04｜画面の作り方を全解説：HTML・CSS・JavaScript

参照：[index.html](../public/index.html)・[styles.css](../public/styles.css)・[app.js](../public/app.js)

## 1. 3つの言語の違い
- **HTML**：何が画面に存在するかを書く（家の骨組み）。
- **CSS**：どう配置して、どんな色・大きさにするかを書く（内装）。
- **JavaScript**：ボタンで何が起きるかを書く（電気・ドアの動き）。

### 例：同じ採点スライダーを3方向から見る

**HTML**：
~~~html
<input type="range" id="score" min="0" max="100" value="50">
~~~
`input`：入力欄。`type="range"`：スライダー。`id="score"`：「scoreという名前で探せるようにする」。`min/max`：選べる範囲。`value`：初期値。

**CSS**：
~~~css
input[type=range] {
  width: 100%;
  accent-color: #121212;
}
~~~
幅を親の要素いっぱいにし、操作部分の色を黒系にします。

**JavaScript**：
~~~javascript
$('score').addEventListener('input', e => {
  $('scoreText').textContent = e.target.value;
});
~~~
スライダーが動くたびに、`scoreText` というHTML要素の文字を更新します。

## 2. 画面の部品を見つける
`index.html` には主に以下があります。

| 画面の場所 | HTMLの目印 | 対応する処理 |
|---|---|---|
| 最上部 | `header.topbar` | タイトルとナビゲーション |
| 鑑賞画面 | `main#gallery` | 表示する作品と採点 |
| 左側の目盛り | `#rulerLines` | `renderRuler()` |
| 作品番号 | `#counter` | `renderArtwork()` |
| 前へ／次へ | `#previous` ／ `#next` | `jump()` |
| 画像本体 | `img#artImage` | `renderArtwork()` |
| 点数 | `input#score` | `saveRating()` |
| 理由 | `select#reason` | `saveRating()` |
| 再評価 | `dialog#revealDialog` | `openReveal()` |
| 2作品比較 | `main#pair` | `pickPair()` |
| 集計画面 | `main#results` | `updateStats()` |

`id` は**その画面の中で一意な名札**です。JavaScriptはその名札で部品を探します。

## 3. 手描きのUIをCSSに置き換えたところ
スケッチには、左右に広い余白、中央の大きな絵、左側の目盛り、上の枚数、下のスライダーがありました。

`styles.css` を開くと：
- `:root`：全体で共通して使う色（例 `--ink` は文字色）。
- `.gallery-view`：メイン画面を左の目盛りと中央作品の2列にする。
- `.ruler`：左の目盛りの領域。
- `.art-frame img`：絵の大きさや表示方法。
- `.stage-top`：矢印と `01 / 50` を並べる。
- `.rating-panel`：下の評価欄。
- `@media`：幅の狭い画面でレイアウトを変える。

~~~css
.gallery-view {
  display: grid;
  grid-template-columns: clamp(110px, 17vw, 260px) minmax(0, 1fr);
}
~~~
- `display: grid`：縦横の区画に配置する。
- `grid-template-columns`：左の目盛りと作品本体の幅の配分。
- `clamp(最小,基準,最大)`：画面が伸び縮みしても極端な幅にならない。
- `vw`：画面幅を基準とする単位。

画面を少し調整したいなら、まずCSSだけ変更すると安全です。

## 4. JavaScriptの最初の一行
~~~javascript
const $ = id => document.getElementById(id);
~~~
本来は長い `document.getElementById('score')` を、`$('score')` と短く書くための道具です。

- `const`：後から別のものへ代入しない名前
- `id => ...`：入力を受け取って結果を返す短い関数

## 5. 匿名の評価者IDを作る
~~~javascript
const storageKey = 'ai-art-rating-web-v6';
const session = JSON.parse(localStorage.getItem(storageKey) || '{}');
if (!session.participant) session.participant = crypto.randomUUID();
~~~
初回アクセス時は、そのブラウザにIDがないので新しいUUID（ほぼ重複しないランダムな文字列）を作ります。2回目以降はブラウザに残るIDを再利用します。

**これは本人認証ではありません。** ブラウザの保存内容を消せば新しいIDになり、別のスマートフォンでも別IDが作られます。

## 6. 作品一覧を受け取る：`init()`
最初の起動では `GET /api/artworks` を呼び、結果を `works` という配列に入れます。

~~~javascript
works = await getJSON('/api/artworks');
renderArtwork();
~~~

- `await`：通信の結果が返るのを待つ。
- `getJSON()`：通信してJSONを取得する関数。
- `renderArtwork()`：現在の作品を画面に描く。

`works[0]` は最初の作品、`works[1]` は2枚目です。`index` は今何枚目を表示中かを覚えます。最初は `index = 0`。

## 7. 作品表示：`renderArtwork()`
機能を小さくすると：
~~~javascript
const art = works[index];
$('artImage').src = art.image_url;
$('artTitle').textContent = art.title;
$('score').value = 50;
~~~
- 現在の作品を配列から取り出す。
- 画像のURLをHTMLの `img` にセット。
- タイトルを画面へ書く。
- 新しい作品なので点数を50に戻す。

実際の関数は、現在位置の `01 / 50` 表示、矢印の無効化、採点済みかどうか、理由欄の初期化、判断時間の開始時点も扱います。

## 8. 矢印の動き
~~~javascript
$('previous').addEventListener('click', () => jump(index - 1));
$('next').addEventListener('click', () => jump(index + 1));
~~~
`click` はクリックのイベント。`index - 1` は前の作品、`index + 1` は次です。`jump()` が先頭より前や最後より後へ出ないように調整します。

## 9. 採点の確定
1. `score` の値を読む。
2. 任意の `reason` を読む。
3. `shownAt` と現在時刻の差から `duration_seconds` を計算する。
4. `openReveal()` で制作情報ダイアログを開く。
5. 「そのまま確定」なら `revised_score = null`、「再評価を保存」なら再評価点を入れる。
6. `send('/api/ratings', body)` でサーバーへ送信。
7. 成功したら `session.ratings` に保存し、次の未評価画像を表示。

**「情報を読まずに直接確定」の単独ボタンではなく、現在の実装ではダイアログを経由します。**「そのまま確定」を選ぶと `info_shown=false` の値で保存されます。これは厳密な対照条件への無作為割付を意味しません。

## 10. `fetch()`：通信の中心
~~~javascript
const response = await fetch('/api/ratings', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(body)
});
~~~
- `fetch`：インターネット経由で問い合わせる。
- `method:'POST'`：新しいデータを送る。
- `body`：送る中身。
- `JSON.stringify`：JavaScriptのオブジェクトをJSON文字列に変換する。

通信エラーが返ると、画面にメッセージを出し、採点ボタンを再度押せるようにします。

## 11. 2枚比較
`pickPair()` はランダムに異なる2作品を選び、左右に並べます。`votePair()` でどちらか1つを選び、`POST /api/pair` へ送ります。同じ2作品の組み合わせを再び評価したときは、ブラウザとDBの両方で重複を抑える仕組みです。

ただし、**ランダムに選び直すだけなので既出ペアが再び表示されることがあります。** 本格的な実験の試行順制御は未実装です。

## 12. 結果画面
`updateStats()` が `GET /api/stats` を呼びます。
`renderSummary(stats)` が各表示先に数値を入れます。
`bar()` は棒の長さを `値 ÷ 最大値 × 100%` で計算し、横棒グラフを生成します。

ここでの「あなたの平均」はブラウザ内の `session.ratings`、「全体の平均」はサーバー側の全回答です。後者にはあなた自身の回答も含まれます。

## 13. CSV出力
`exportCSV()` は、ブラウザの `session.ratings` を整形し、CSVファイルとしてダウンロードします。これは**全参加者の個票をSupabaseから取り出す機能ではありません**。

## 14. 自分で改良する練習
- 最初の点数を `50` から `0` へ変えてみる。
- `.art-frame img` の `height` を変えて画像の見え方を観察する。
- ボタンの文言を変える（HTMLだけ）。
- 評価理由の候補を追加したい場合は、**HTMLの選択肢とPythonの許可リストを両方**修正する。
- 変更後にブラウザを更新し、エラーがないことを確認する。

**大切**：CSSの色や余白を変えることと、研究データの評価基準を変えることは影響の大きさが違います。実験途中で点数の範囲や理由の選択肢を変更する場合は研究記録にも残してください。
