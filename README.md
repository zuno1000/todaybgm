# 今日の作業テーマ曲(todaybgm)

**「アプリを開いた瞬間、今日の作業用BGMが1曲決まっている」**

選曲に迷う時間をゼロにする、作業用BGMレコメンドWebアプリ(プロトタイプ v0.1)。

## 特徴

- ページを開くと「今日のテーマ曲」が1曲自動で提示される
- YouTube 埋め込みプレイヤーでワンタップ再生
- ★1〜5 の5段階評価。使うほどおすすめが自分好みに近づく(コンテンツベース推薦)
- 事前設定: 好みのジャンル(Lo-fi / ジャズ / ピアノ / 環境音 / ゲームBGM / シンセウェーブ / クラシック)と動画時間
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
- GitHub Pages でホスティング可能な完全静的構成
- 曲カタログ: 全7ジャンル、埋め込み許可を確認済みの動画のみ収録。再生不能を検知した曲は端末側でも自動除外

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
