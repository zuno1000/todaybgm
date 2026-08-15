# 今日の作業テーマ曲(TODAY'S BGM)

**開いた瞬間、今日の一曲が決まっている。**

選曲に迷う時間をゼロにする、無料の作業用BGMレコメンドWebアプリ。

👉 **https://todaybgm.pages.dev/**

![OGP](ogp.png)

## 使い方

1. **開くだけ**: アクセスした瞬間に「今日の1曲」が決まっています。再生ボタンをタップ
2. **設定**: 好きなジャンル(Lo-fi / ジャズ / ピアノ / 環境音 / ゲームBGM / シンセウェーブ / クラシック / ケルト / ファンタジー / 和風 / EDM / かわいい)と動画時間を選ぶと、おすすめが条件に沿います
3. **★評価**: 聴いたら5段階で評価。使うほど、おすすめがあなたの好みに寄り添います(「好み」タブで学習結果のほか、連続日数・総再生時間・実績(あゆみ)・おすすめとの相性(月ごとの推移)も見られます。実績は達成すると次の段階へ進化し、バッジをタップすると進捗の詳細が開きます)
4. **探す**: 気分ミキサー(朝↔夜 / アコースティック↔電子音 / ゆったり↔アップテンポ+雨音)で、今の気分の1曲を能動的に探せます。曲名・ジャンル名での検索もできます
5. **作業**: BGMを流しながら使えるポモドーロタイマー(25分/50分)と、やることリスト。日ごとの作業時間・完了数は「作業のあゆみ」で振り返れます
6. **履歴**: 聴いた曲がカレンダーに記録され、いつでもタップで再生できます
7. **同期(任意)**: Googleでログインすると、評価・履歴・設定・作業の記録をあなた自身のGoogleドライブ経由で他の端末と同期できます
8. **共有**: Xで共有 / 画像カード(QR付き)で共有 / YouTubeで開く(再生位置を引き継ぎ)。画像のQRを読み込むと、このアプリでその曲がそのまま開きます(`?v=動画ID` のリンクでも同じことができます)。「好み」タブからは**音楽プロフィールカード**(MBTI風の4文字タイプ+聴き方の4軸)と**実績カード**も画像で共有できます

スマホでは**ホーム画面に追加**(PWA)すると、アプリのように全画面で使えます。PC(幅1024px以上)では左サイドバー+2カラムのデスクトップレイアウトになります。

## プライバシー(要点)

- アカウント登録不要。**開発者のサーバーは存在せず、データ収集もありません**
- 評価・履歴・設定は端末内(localStorage)にのみ保存されます
- 任意の同期を有効にした場合も、保存先は**あなた自身のGoogleドライブのアプリ専用領域**(開発者はアクセスできません)
- 詳細: [プライバシーポリシー](https://todaybgm.pages.dev/privacy)

## 既知の制限

- 「YouTubeで開く」の再生位置引き継ぎは、YouTubeアプリが同じ動画を既に開いている場合は効きません(YouTubeアプリ側の仕様)
- スマホのブラウザ内の埋め込み再生では広告を消せません。YouTube Premiumの方は設定の「常にYouTubeアプリで開く」をオンにすると広告なし+バックグラウンド再生ができます
- 横向きの自動全画面はブラウザのUIまでは消せません。動画だけの全画面はプレイヤー右下の全画面ボタン、より没入するならホーム画面に追加(PWA)がおすすめです

## コンテンツについて

曲カタログはYouTube上の公開動画を機械的に収集・検証して掲載しています(動画の保存・再配布はしません)。そのため、**AI生成の音楽・サムネイルを含む動画や、無断転載が疑われる動画(ゲーム音楽等)が混ざる場合があります**。お気づきの際は下記フィードバック窓口へご連絡ください。確認のうえカタログから削除し、自動更新でも再追加されないよう除外リストで管理します。詳細は[プライバシーポリシー](https://todaybgm.pages.dev/privacy)の「コンテンツ(曲カタログ)について」をご覧ください。

## フィードバック

不具合報告・要望は [GitHub Issues](https://github.com/zuno1000/todaybgm/issues) または todaybgm.contact@gmail.com へ。

---

# 開発者向け

## 技術構成

- HTML 1枚(Vanilla JS、フレームワークなし)+ songs.json(曲カタログ)
- YouTube IFrame Player API / Google Identity Services + Drive API(任意同期)
- 完全静的構成。Cloudflare Pages でホスティング(mainへのpushで自動デプロイ。GitHub Pages等でも動作可)
- 曲カタログ: 全12ジャンル・約720曲。埋め込み許可を確認済みの動画のみ収録。再生不能を検知した曲は端末側でも自動除外
- セキュリティヘッダ: `_headers` でCSP(強制モード)等を設定。**許可先を追加する時は一度 Report-Only に戻して観察してから強制化すること**

## 曲カタログの更新(scripts/update_songs.py)

```
python scripts/update_songs.py [--max-per-genre 60] [--per-query 25] [--dry-run]
```

- 既存曲の死活チェック(再生不能になった動画を削除)+ ジャンル別クエリでの新曲検索・検証・追加
- 同一チャンネルはジャンル内3曲まで(多様性の担保)
- **NGリスト**: `scripts/ng_ids.json` にIDを追記すると、その曲をカタログから削除し、以後の自動更新でも再追加しない(歌もの・不適切コンテンツの恒久除外用)。タイトルに歌詞・ボーカルを明記した動画は自動追加時に除外される
- 環境変数 `YOUTUBE_API_KEY` があれば YouTube Data API v3、なければスクレイピングで動作
- 検索クエリは `scripts/queries.json` で管理(ここを編集すると探すジャンル・傾向を変えられる)
- GitHub Actions(`.github/workflows/update-songs.yml`)が毎週土曜 6:00 JST に自動実行。
  リポジトリの Secrets に `YOUTUBE_API_KEY` の登録が必要

### プライバシー設計

- リポジトリに置くのは「誰の好みでもない汎用の曲カタログ+検索クエリ設定」のみ
- 個人の評価・設定・履歴は端末の localStorage から出ない(送信処理が存在しない)
- 「好みに寄せる」のは端末内のレコメンド、「母数を増やす」のがActions、と完全分離

## ローカル確認

```
cd todaybgm
python -m http.server 8000
# → http://localhost:8000
```

※ file:// 直接開きでも動作するが、YouTube IFrame API の挙動確認は http 経由推奨。

## セルフテスト(tests/)

コアロジック(レコメンド・履歴・同期マージ・探す・リセット・エッジケース)の常設テスト。**リリース(push)前に全実行すること。**

```
powershell -ExecutionPolicy Bypass -File tests\run.ps1
# → RESULT: ALLPASS-<件数> / ALL TESTS PASSED なら合格(exit 0)
```

- 別ポート(8765)+使い捨てブラウザプロファイルで実行するため、localhost:8000 の開発データには影響しない
- `-BrowserPath` でChrome等の別Chromiumブラウザでも実行できる(既定は自動検出)
- 手動で見る場合: `python -m http.server 8765` → http://localhost:8765/tests/ (結果が表形式で出る)
- テストページは localStorage を破壊的に書き換えるため **localhost 以外では起動しないガード付き**(本番URLで開いても実行されない)

## データ(localStorage)

| キー | 内容 |
|------|------|
| `bgm_settings` | 選択ジャンル配列、希望時間クラス |
| `bgm_ratings` | `{videoId: {rating, ratedAt}}` |
| `bgm_daily` | 当日の日付・提示済みID・現在の1曲 |
| `bgm_recent` | 直近3日間の提示履歴(再提示減衰用) |
| `bgm_dead` | 再生エラーになった動画ID(以後の候補から自動除外) |
| `bgm_plays` | 日別の再生履歴 `{date: {first, plays[]}}`(カレンダー・履歴用) |
| `bgm_songmeta` | 再生・評価した曲のタイトル/ジャンル控え(カタログ削除後の履歴表示用) |
| `bgm_playmode` | 曲が終わったら: `next`/`repeat`/`stop` |
| `bgm_todaymode` | 「今日の曲」の更新タイミング(`{mode, hours}`) |
| `bgm_listen` | 日別の実再生時間 `{date: 累計秒}`(「好み」タブの統計・実績用) |
| `bgm_openapp` | 常にYouTubeアプリで開く |
| `bgm_autoplay` | アプリを開いたら「今日の曲」を自動再生(ブラウザの自動再生制限でブロックされた場合は何もしない) |
| `bgm_work` | 日別の作業実績 `{date: {sec: 作業秒, pomo: 完了数}}`(「作業」タブのあゆみ用) |
| `bgm_todos` | やることリスト `{id: {text, done, createdAt, doneAt, updatedAt, deleted}}`(削除はトンボストーン。完了・削除から30日で掃除) |
| `bgm_pomo` | ポモドーロタイマーの進行状態(端末ローカル・同期しない) |
| `bgm_fshint` | 全画面ヒントを表示済みか |
| `bgm_sync` | データ同期の連携状態(`{linked, updatedAt, lastSync, ratingsResetAt, playsResetAt, workResetAt, dirtySince}`)。`dirtySince`=未同期のローカル変更が発生した時刻(同期成功で0。同期リマインダーの判定に使用) |

## データ同期(端末間・Googleドライブ)の設定

ログイン(Googleアカウント)で、評価・履歴・設定を**ユーザー自身のGoogleドライブのアプリ専用領域(appDataFolder)**経由で端末間同期できます。サーバー不要・無料で、データは開発者や第三者のサーバーには保存されません。

クライアントIDは**本番用と localhost 開発用の2つ**(別GCPプロジェクト)に分離しており、`index.html` がホスト名で自動切替します(`localhost`/`127.0.0.1` → 開発用、それ以外 → 本番用)。自分用に設定するには:

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成(本番用・開発用の2つ)
2. 各プロジェクトで「APIとサービス」→「ライブラリ」から **Google Drive API** を有効化
3. 「OAuth 同意画面」を設定(User type: 外部)。スコープに `.../auth/drive.appdata` を追加
   - 開発用は公開ステータス「テスト」のままでOK(テストユーザーに自分のGoogleアカウントを追加)
4. 「認証情報」→「OAuth クライアント ID」を作成(種類: **ウェブアプリケーション**)
   - **承認済みの JavaScript 生成元**: 本番用クライアントには公開URL(例: `https://todaybgm.pages.dev`)、開発用クライアントには `http://localhost:8000` を追加
5. 発行された「クライアント ID」(`xxxx.apps.googleusercontent.com`)を、`index.html` の
   `GOOGLE_CLIENT_ID_PROD` / `GOOGLE_CLIENT_ID_DEV` に貼り付けてコミット

補足:
- 同期対象は `bgm_settings` / `bgm_ratings` / `bgm_plays` / `bgm_dead` / `bgm_openapp` / `bgm_playmode` / `bgm_todaymode` / `bgm_songmeta` / `bgm_listen` / `bgm_work` / `bgm_todos` / `bgm_autoplay`(`bgm_daily`・`bgm_recent`・`bgm_pomo` は端末ごとに独立。`bgm_listen`・`bgm_work` は日別maxでマージ=再マージでの二重計上を防ぐ。`bgm_todos` はIDごとに新しい方が勝ち、削除はトンボストーンで伝播)
- 競合は非破壊マージ(評価=`ratedAt`が新しい方、履歴=和集合、設定=更新時刻が新しい方)+リセット時刻のトンボストーン
- `drive.appdata` は現在のGoogleの分類では**非機密スコープ**(アプリ専用フォルダのみアクセス)。公開ステータスを「本番」にしてもスコープ審査は不要で、必要なのはブランディング検証のみ(2026-07確認)。開発用プロジェクトは「テスト」のままで審査もブランディングも不要
