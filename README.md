# 今日の作業テーマ曲(todaybgm)

**「アプリを開いた瞬間、今日の作業用BGMが1曲決まっている」**

選曲に迷う時間をゼロにする、作業用BGMレコメンドWebアプリ(プロトタイプ v0.1)。

## 特徴

- ページを開くと「今日のテーマ曲」が1曲自動で提示される
- YouTube 埋め込みプレイヤーでワンタップ再生
- ★1〜5 の5段階評価。使うほどおすすめが自分好みに近づく(コンテンツベース推薦)
- 事前設定: 好みのジャンル(Lo-fi / ジャズ / ピアノ / 環境音 / ゲームBGM / シンセウェーブ / クラシック / ケルト音楽 / ファンタジー / 和風)と動画時間
- 「別の曲にする」再抽選(同日中は既出曲を除外)
- 全データは端末内 localStorage のみ。サーバー送信なし・維持費0円

## 特徴(v0.2)

- 📊 「好み」タブ: 評価から学習したジャンル/ムード親和度をバーで可視化
- 🔄 曲カタログ(songs.json)の自動更新: 週1のGitHub Actionsが死活チェック+新曲追加
- 📱 「YouTubeアプリで開く」: YouTube Premium ならアプリ側でバックグラウンド再生できる
- 🎨 アプリアイコン+manifest 同梱(ホーム画面に追加可能。生成は scripts/make_icon.py)

## 技術構成

- HTML 1枚(Vanilla JS、フレームワークなし)+ songs.json(曲カタログ)
- YouTube IFrame Player API
- 完全静的構成。Cloudflare Pages でホスティング(公開URL: https://todaybgm.pages.dev/ 。mainへのpushで自動デプロイ。GitHub Pages等でも動作可)
- 曲カタログ: 全10ジャンル、埋め込み許可を確認済みの動画のみ収録。再生不能を検知した曲は端末側でも自動除外

## 曲カタログの更新(scripts/update_songs.py)

```
python scripts/update_songs.py [--max-per-genre 40] [--per-query 12] [--dry-run]
```

- 既存曲の死活チェック(再生不能になった動画を削除)+ ジャンル別クエリでの新曲検索・検証・追加
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

## データ(localStorage)

| キー | 内容 |
|------|------|
| `bgm_settings` | 選択ジャンル配列、希望時間クラス |
| `bgm_ratings` | `{videoId: {rating, ratedAt}}` |
| `bgm_daily` | 当日の日付・提示済みID・現在の1曲 |
| `bgm_recent` | 直近3日間の提示履歴(再提示減衰用) |
| `bgm_dead` | 再生エラーになった動画ID(以後の候補から自動除外) |
| `bgm_plays` | 日別の再生履歴 `{date: {first, plays[]}}`(カレンダー・履歴用) |
| `bgm_playmode` | 曲が終わったら: `next`/`repeat`/`stop` |
| `bgm_openapp` | 常にYouTubeアプリで開く |
| `bgm_sync` | データ同期の連携状態(`{linked, updatedAt, lastSync}`) |

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
- 同期対象は `bgm_settings` / `bgm_ratings` / `bgm_plays` / `bgm_dead` / `bgm_openapp` / `bgm_playmode`(`bgm_daily`・`bgm_recent` は端末ごとに独立)
- 競合は非破壊マージ(評価=`ratedAt`が新しい方、履歴=和集合、設定=更新時刻が新しい方)
- `drive.appdata` は現在のGoogleの分類では**非機密スコープ**(アプリ専用フォルダのみアクセス)。公開ステータスを「本番」にしてもスコープ審査は不要で、必要なのはブランディング検証のみ(2026-07確認)。開発用プロジェクトは「テスト」のままで審査もブランディングも不要
