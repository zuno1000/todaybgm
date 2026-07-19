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

## 技術構成

- 単一 HTML(Vanilla JS、フレームワークなし)
- YouTube IFrame Player API
- GitHub Pages でホスティング可能な完全静的構成
- 曲マスタ: 36曲(全7ジャンル、埋め込み許可を確認済みの動画のみ収録)

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
