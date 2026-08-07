# Sound + BGM Generator for Windows

1. Windows で `setup.bat` を一度だけ実行します。
2. `start.bat` をダブルクリックします。
3. ブラウザで「効果音」または「BGM」を選んで作ります（WAVで保存可能）。
4. CLI: `python tools\generate_audio.py --mode music --prompt "quiet piano ambient for rainy-day work, no vocals" --duration 30 --json`
5. 初回は Hugging Face で [small-sfx](https://huggingface.co/stabilityai/stable-audio-3-small-sfx) と `small-music` の各モデルページを開き、ゲート・ライセンスを承認後、PowerShellで `huggingface-cli login` を実行します。トークンをこのリポジトリのファイルへ書かないでください。

`small-sfx` は効果音、`small-music` はBGM/音楽用です。選択された一方だけを遅延ロードし、切替時には前のモデルを解放します。既定値は効果音5秒、BGM30秒、WAV、`127.0.0.1:8600` です。`POST /api/generate` は `mode` 省略時に従来通り効果音として扱います。

日本語はローカルOpenAI互換翻訳サーバー（既定 `http://127.0.0.1:64652/v1`）が必要です。画面に利用可否が出ます。英語は翻訳サーバーなしで生成でき、履歴では実際に使った英語プロンプトを確認できます。

## CLI

サービスを `start.bat` で起動してから実行します。未起動時は具体的な起動方法を表示します。`--output C:\path\file.wav` で保存先を指定、`--json` で機械可読出力にします。

## 注意

各Stable AudioモデルのHugging FaceゲートとStability AIライセンス条件に従ってください。元リポジトリのアプリコードに明確なライセンスはないため、この変更でアプリコードの再配布ライセンスを新設していません。公開・再配布前には権利者と各依存・モデルの条件を確認してください。
