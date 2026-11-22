# 07｜エラー対処辞典：「何が起きた？」から直せる

エラーに遭っても、**どの段階か** が分かれば原因を絞り込めます。
最初に見る順序：①ブラウザの画面 → ②APIのURL → ③Vercelのログ → ④Supabaseの状態。

## 0. 最初に試す4つ
1. 表示を更新する（Safariでは `⌘ + R`）。
2. `/api/health` のJSONを直接開いてみる。
3. `/api/stats` を開き、データベースが動くかを見る。
4. Vercelの **Deployments** と **Logs** で最新のエラーを読む。

**秘密鍵の中身をスクリーンショットや質問文に含めないこと。**

## 1. 「ページが開かない」
- URLの末尾やスペルを確かめる。
- VercelのDeploymentsで **READY** になっているか確認。
- Vercel Authenticationのログイン画面なら、対象のデプロイにアクセス制限が付いている可能性がある。
- 同じ名前の別Vercelプロジェクトを見ていないか確認。

## 2. HTTP 404（Not Found）
意味：「頼まれたページやファイルがない」。
- GitHubで `public/index.html` と `public/app.js` が存在するか。
- Root Directoryが正しいか（`app.py` と `public` を持つルート）。
- 画像が欠ける場合、`public/images/art_001.jpg` のようなファイル名がCSVと一致するか。
- GitHub連携か、直接デプロイかを確認。静的ファイルの配置が異なる場合がある。

## 3. HTTP 500 / FUNCTION_INVOCATION_FAILED
意味：「Pythonが動く途中で落ちた」。

実際に遭遇した事例：
~~~text
RuntimeError: Directory '/var/task/public' does not exist
~~~
最初のVercel本番デプロイでは、Pythonの `StaticFiles(directory=PUBLIC)` がサーバー内にないフォルダを開こうとして500になりました。

**採用した修正**（現在の `app.py`）：
~~~python
if IS_HOSTED:
    @app.get('/')
    def frontend_redirect():
        return RedirectResponse(url='/index.html', status_code=302)
else:
    app.mount('/', StaticFiles(directory=PUBLIC, html=True), name='frontend')
~~~
Vercelでの静的ファイル配信と、Macのローカル配信を分けました。これで再デプロイ後に `/api/health` は200を返すようになりました。

## 4. HTTP 503：データベース未設定
公開環境に `SUPABASE_URL` または `SUPABASE_SECRET_KEY` がない状態で採点を保存しようとすると発生します。

直し方：
1. Vercel → Settings → Environment Variablesへ。
2. **Keyの名前** を確認（余計な空白に注意）。
3. Productionで動かすならProduction環境に両方あるか確認。
4. 設定後は新しいデプロイを実行。

`SUPABASE_SECRET_KEY` はブラウザへ出さないでください。

## 5. HTTP 502：Supabaseとの接続が失敗
考えられる原因：
- Supabase URLの入力ミス。
- Secret keyが無効または別プロジェクト用。
- テーブルやRPCがまだ作成されていない。
- Supabaseプロジェクトが停止中。
- APIへの接続障害。

対処：
1. `/api/health` だけでなく `/api/stats` を確認。
2. SupabaseのProject Dashboardで起動状態を確認。
3. `artworks`・`ratings`・`pair_votes` があるか確認。
4. `art_rating_summary()` 関数と権限を確認。
5. Vercelのログを確認。**秘密鍵をログへ印字しない。**

## 6. HTTP 409：重複して保存しようとした
たとえば同じ参加者が `ART-001` を2回送信した場合、DBの主キーで拒否されます。
2作品比較でも同じ組み合わせは重複禁止です。
*通常のアプリ利用では、保存済みの作品へ再投稿しないようにしています。*

原因が「初回なのに409」のとき：
- 以前そのブラウザで採点した。
- 別のタブで同時に送った。
- ブラウザの保存状態とサーバーの状態がずれた。
**本番データを削除して無理に解消しない**こと。

## 7. HTTP 422：入力がルールに合わない
例：`score: 101`、UUIDの形式が不正、判断時間が3600秒超など。
`app.py` の `class Rating(BaseModel)` を読んで入力条件を確認してください。

## 8. 「画像だけ表示されない」
- 作品一覧APIの `image_url` を開いて確認。
- GitHub上の `public/images/` に50枚があるか。
- Macのローカルでは `/images/art_001.jpg` を試す。
- 直接デプロイ版はGitHubの公開画像URLを参照するため、**GitHubリポジトリをPrivateへ変更すると画像表示が壊れる可能性**があります。
- ブラウザの開発者ツール「Network」で画像HTTPレスポンスを見ると原因が分かります。

## 9. 「画面は出るのに評価が保存できない」
`index.html` や `styles.css` だけ正常でも、API側が動いていない場合があります。
- `/api/health` が200か。
- `/api/stats` が200か。
- VercelのProductionに秘密鍵が存在するか。
- 対象のDBで `ratings` が存在するか。
- 同じ作品に以前採点していないか。

## 10. 「GitHubにアップロードしたのに本番が変わらない」
**このアプリの初回公開はGitHub連携ではなくVercelへの直接デプロイ**だからです。
GitHubの変更が本番へ自動反映されるとは限りません。
VercelのプロジェクトにGitHubを接続し、正しいブランチ（通常 `main` ）を選び、**新しいデプロイが作成されたこと**を確認してください。

## 11. GitHub API 429 / Rate limited
一定時間にAPIを呼びすぎたため一時制限されています。
- 短時間に繰り返し何度も再試行しない。
- 制限が解除されるまで間隔を空ける。
- 必要ならGitHub連携の権限・接続状況を確認。
- 2026-11-23の初回公開時は、これを回避するためVercelへ直接配置しました。

## 12. Pythonコマンドが見つからない
`python: command not found` → `python3 --version` を確認。
`uvicorn: command not found` → 仮想環境を有効化し、`python -m pip install -r requirements.txt` を再実行。
`ModuleNotFoundError` → 正しい`.venv`に必要なパッケージが入っているか確認。

## 13. GitHubへ秘密鍵を誤って登録したら
1. **直ちにSupabase側で鍵をローテーション／失効**する。
2. Vercelの環境変数を新しい鍵に更新し、再デプロイ。
3. GitHubの該当ファイルだけでなく、履歴にも秘密鍵が残ることを理解する。
4. 必要に応じてGitHubの秘密情報削除手順や専門家へ相談。

**単にコミットで削除しても、漏洩済みの鍵は安全になりません。**

## 14. 原因を説明するテンプレート
質問・バグ報告には次の4点があると直しやすいです。
- どの画面・URLで？
- 何をクリックしたら？
- 期待した結果は？
- 実際のエラー（**鍵・個票・個人情報は伏せる**）は？

例：「`/api/stats` を開くと502。Vercelのログは接続エラー。`/api/health` は200でmode=supabase」。
