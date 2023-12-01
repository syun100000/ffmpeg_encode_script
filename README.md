# ffmpeg_encode_script
フォルダ内のファイルをまとめてffmpegで変換するスクリプト
GitHub Copilot: # service.py

このPythonスクリプトは、指定された入力ファイルをエンコードするためのものです。
私がh265に変換するために作成しましたが、他のエンコードにも使用できます。
お好みで変更してください。
## 使用方法

1. スクリプトを実行します。
2. プロンプトが表示されたら、エンコードするファイルを確認します。
3. 'y'を入力してエンコードを開始するか、'n'を入力してエンコードを中止します。
4. エンコードが完了すると、出力ディレクトリにエンコードされたファイルが保存されます。

## config.jsonについて
このファイルは、デフォルト値を設定するためのものです。
## 関数

- `main()`: スクリプトのメインエントリーポイントです。ここから他の関数が呼び出されます。
- `get_bitrate(ffmpeg, input_file)`: 入力ファイルのビットレートを取得します。
- `encode_video(ffmpeg, input_file, output_file, input_bitrate, quality, resolution, overwrite)`: 入力ファイルをエンコードします。

## 注意事項

- エンコードを中止すると、その時点でのエンコードは完了しません。
- `delete`が`True`に設定されている場合、エンコード後に元のファイルは削除されます。

## 依存関係

このスクリプトはffmpegを必要とします。