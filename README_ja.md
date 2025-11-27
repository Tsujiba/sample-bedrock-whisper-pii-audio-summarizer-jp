# Sample Bedrock Whisper PII Audio Summarizer

このプロジェクトは、音声ファイルのアップロード、自動文字起こし、個人情報の編集、要約生成を行うシンプルなインターフェースを提供します。WAVファイルのアップロードを処理し、AWS BedrockとWhisper AIで処理し、機密情報を安全に編集した要約コンテンツを表示するモダンなWebアプリケーションを作成します。

## プロジェクト構成

- `frontend-ui/` - ユーザーインターフェース用のReactフロントエンドアプリケーション
- `backend-cdk/` - AWS CDKインフラストラクチャとLambdaバックエンド
- `utils/` - 音声変換とPII編集のためのユーティリティスクリプト
- `tests/` - 機能検証のためのテストスクリプト

## ユーザーフロー

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│                │     │                │     │                │
│  音声または動画  │────▶│   処理と       │────▶│    要約の      │
│ ファイルアップロード│     │   編集         │     │    表示        │
│                │     │                │     │                │
└────────────────┘     └────────────────┘     └────────────────┘
```

1. ユーザーがインターフェースを通じて音声/動画ファイルをアップロード
2. ファイルがAWSバックエンドで処理される:
   - 音声抽出（動画の場合）
   - Whisper AIによる文字起こし
   - Bedrock Guardrailsによる個人情報の編集
   - 要約生成
3. 編集されたコンテンツがUIに表示される

## ファイル要件

### WAV形式が必要

現在、アプリケーションはWAV形式の音声ファイルのみを受け付けます。MP4やその他の形式がある場合は、まず変換する必要があります。

### MP4からWAVへの変換

FFmpegを使用してMP4ファイルをWAV形式に変換できます:

```bash
# FFmpegのインストール（まだインストールしていない場合）
# macOS
brew install ffmpeg

# Ubuntu/Debian
# sudo apt-get install ffmpeg

# MP4からWAVへの変換
ffmpeg -i input-file.mp4 -vn -acodec pcm_s16le -ar 44100 -ac 2 output-file.wav
```

または、付属のユーティリティスクリプトを使用できます:

```bash
python utils/convert_audio.py input-file.mp4 output-file.wav
```

## 機能

### シンプルなユーザーインターフェース

- **簡単なアップロード**: WAV音声ファイルをドラッグ&ドロップまたはクリックしてアップロード
- **リアルタイム進捗**: 文字起こしと要約生成をモニタリング
- **クリーンな結果表示**: 機密情報が編集された最終要約を表示

### プライバシー保護

- **自動PII編集**: 個人を特定できる情報が自動的に検出され編集されます
- **保護されるコンテンツタイプ**:
  - 氏名と個人の身元
  - 電話番号
  - メールアドレス
  - 物理的な住所
  - 財務情報
  - その他の機密情報

- **AWS Bedrock Guardrails**: アプリケーションは[AWS Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html)を使用してエンタープライズグレードのPII検出と編集を行います
  - 詳細な設定手順については[backend-cdk README](backend-cdk/README.md)を参照してください

### AWS統合

- 安全で正確なPII編集のためにAWS Bedrockを使用
- 高品質な音声文字起こしのためにWhisper AIを活用
- スケーラビリティとパフォーマンスのためのサーバーレスアーキテクチャ

## 完全デプロイメントガイド

このセクションでは、バックエンドとフロントエンドの両コンポーネントをデプロイし、アプリケーションをテストするための詳細な手順を提供します。

> **注意**: このリポジトリにはサンプル音声ファイルは含まれていません。テストと使用のために独自のWAVファイルを用意する必要があります。

### 前提条件

- AWS CLIがインストールされ、適切な権限で設定されていること
  ```bash
  aws configure
  ```
- Node.js 14.x以降がインストールされていること
- AWS CDK CLIがグローバルにインストールされていること
  ```bash
  npm install -g aws-cdk
  ```
- ユーティリティスクリプト用のPython 3.8以上

### ステップ1: リポジトリのクローンと準備

```bash
# リポジトリのクローン
git clone https://github.com/aws-samples/sample-bedrock-whisper-pii-audio-summarizer.git

# プロジェクトディレクトリに移動
cd sample-bedrock-whisper-pii-audio-summarizer
```

### ステップ2: バックエンドインフラストラクチャの設定とデプロイ

**重要**: デプロイ前に、WhisperエンドポイントとBedrock Guardrailを設定する必要があります。

**Whisperエンドポイントの設定**:

アプリケーションは、AWS Bedrock MarketplaceからデプロイされたSageMaker Whisperエンドポイントが必要です。デプロイ前にこのエンドポイントを設定する必要があります:

1. `backend-cdk/lib/audio-summarizer-stack.ts`を開く
2. WhisperTranscriptionFunction宣言を見つけ、WHISPER_ENDPOINT値を更新する:
   ```typescript
   environment: {
     // その他の変数...
     WHISPER_ENDPOINT: 'your-whisper-endpoint-name' // 必須 - エンドポイント名をここに設定
   }
   ```
3. デプロイ前にファイルを保存する

Whisperエンドポイントの設定の詳細については、[backend-cdk README](backend-cdk/README.md#whisper-endpoint-configuration)を参照してください。

**Bedrock Guardrailの設定**:

アプリケーションはPII検出と編集のためにAWS Bedrock Guardrailsが必要です。デプロイ前にguardrailを設定する必要があります:

1. `backend-cdk/lib/audio-summarizer-stack.ts`を開く
2. BedrockSummaryFunction宣言を見つけ、GUARDRAIL_ID値を更新する:
   ```typescript
   environment: {
     // その他の変数...
     GUARDRAIL_ID: 'arn:aws:bedrock:REGION:ACCOUNT_ID:guardrail/YOUR_GUARDRAIL_ID' // 必須 - guardrail ARNをここに設定
   }
   ```
3. デプロイ前にファイルを保存する

Bedrock guardrailの作成と設定の詳細については、[backend-cdk README](backend-cdk/README.md#pii-redaction-with-aws-bedrock-guardrails)を参照してください。

これらの必要なコンポーネントの設定に関する詳細な手順については、以下の設定セクションを参照してください。

```bash
# backend CDKディレクトリに移動
cd backend-cdk

# 依存関係のインストール
npm install

# CDKのブートストラップ（AWSアカウント/リージョンごとに1回のみ必要）
npm run cdk bootstrap aws://$(aws sts get-caller-identity --query 'Account' --output text)/$(aws configure get region)

# 必要な値を設定した後、スタックをデプロイ
npm run cdk deploy
```

**重要**: デプロイが完了すると、CDKはいくつかの値を出力します。以下をメモしてください:
- `ApiEndpoint` - API Gateway URL（例: `https://xxxxxxxxxxxx.execute-api.us-west-2.amazonaws.com/prod/`）
- `CloudFrontURL` - CloudFrontディストリビューションURL（例: `xxxxxxxxxx.cloudfront.net`）
- フロントエンドホスティング用のS3バケット名（例: `frontend-ui-websitebucketXXXXXXXX`）

バックエンドのデプロイでは以下が作成されます:
- アップロードと処理結果を保存するためのS3バケット
- 音声処理とPII編集のためのLambda関数
- リクエストを処理するためのAPI Gatewayエンドポイント
- 安全なアクセスのためのIAMロールとポリシー
- フロントエンドをホスティングするためのCloudFrontディストリビューション

### ステップ3: フロントエンドの設定とデプロイ

```bash
# フロントエンドディレクトリに移動
cd ../frontend-ui

# 依存関係のインストール
npm install
```

**フロントエンド設定の更新**:

`src/config.js`ファイルを編集して、API Gatewayエンドポイントを指定します:

```javascript
// CDK出力から実際のAPIエンドポイントに置き換える
export const API_GATEWAY_ENDPOINT = 'https://xxxxxxxxxxxx.execute-api.us-west-2.amazonaws.com/prod';
```

**フロントエンドのビルドとデプロイ**:

```bash
# アプリの本番バージョンをビルド
npm run build

# CDK出力からS3バケット名を取得
UIBUCKET=$(aws cloudformation describe-stacks --stack-name SampleBedrockWhisperPiiAudioSummarizerStack --query "Stacks[0].Outputs[?OutputKey=='UIBucketName'].OutputValue" --output text)
echo "Frontend UI bucket: $UIBUCKET"

# CDK出力からのバケット名を使用してS3バケットにアップロード
aws s3 sync build/ s3://$UIBUCKET/

# CloudFrontディストリビューションIDを取得
CLOUDFRONT_URL=$(aws cloudformation describe-stacks --stack-name SampleBedrockWhisperPiiAudioSummarizerStack --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" --output text)
CLOUDFRONT_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?DomainName=='$CLOUDFRONT_URL'].Id" --output text)
echo "CloudFront distribution ID: $CLOUDFRONT_ID"

# CloudFrontキャッシュを無効化して変更をすぐに反映
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_ID --paths "/*"
```

### ステップ4: デプロイメントの検証とテスト

1. **アプリケーションへのアクセス**:
   - Webブラウザを開き、CloudFront URLにアクセス
   - 例: `https://xxxxxxxxxx.cloudfront.net`

2. **WAVファイルでテスト**:
   - テスト用のWAVファイルを準備するか、変換手順を使用してMP4をWAVに変換
   - Webインターフェースのアップロードボタンをクリック
   - WAVファイルを選択してアップロード
   - アップロードの進捗に続いて処理ステータスが表示されるはずです

3. **処理の成功を確認**:
   - 処理が完了すると（通常1〜3分）、以下が表示されます:
     - 音声ファイルの文字起こし
     - コンテンツの要約
     - PIIは自動的に編集されているはずです

4. **問題が発生した場合はCloudWatchログを確認**:
   ```bash
   # Lambda関数のログを表示（FUNCTION_NAMEを実際の関数名に置き換え）
   aws logs get-log-events --log-group-name /aws/lambda/FUNCTION_NAME --log-stream-name $(aws logs describe-log-streams --log-group-name /aws/lambda/FUNCTION_NAME --order-by LastEventTime --descending --limit 1 --query 'logStreams[0].logStreamName' --output text)
   ```

### デプロイメント問題のトラブルシューティング

- **CloudFormationエラー**: スタックのデプロイエラーについてはAWS CloudFormationコンソールを確認
- **S3アップロードの問題**: 正しい権限とバケット名があることを確認
- **フロントエンドが更新されない**: ハードリフレッシュ（Ctrl+Shift+R）を試すか、CloudFront無効化ステータスを確認
- **Lambda関数の失敗**: エラーメッセージについてCloudWatchログを確認
- **API Gateway設定**: CORS設定が適切に設定されていることを確認

## デプロイされたアプリケーションのテスト

1. **アプリケーションへのアクセス**
   - ブラウザを開き、デプロイ出力のCloudFront URLにアクセス
   - 例: `https://xxxxxxxxxx.cloudfront.net`

2. **WAVファイルのアップロード**
   - アップロードボタンをクリックするか、WAVファイルをアップロードエリアにドラッグ&ドロップ
   - ファイルはWAV形式である必要があります（必要に応じて上記の変換手順を参照）
   - テストには、音声を含む短い音声クリップ（30〜60秒）を使用してください

3. **処理のモニタリング**
   - ファイルが処理されている間、アプリケーションは進捗インジケータを表示します
   - これには、アップロード、文字起こし、PII編集、要約生成が含まれます
   - 処理には通常、ファイルサイズに応じて1〜3分かかります

4. **結果の表示**
   - 処理が完了すると、要約が表示されます
   - すべての機密情報は自動的に編集されます
   - 文字起こしテキストとコンテンツの要約が表示されるはずです

## トラブルシューティング

- **ファイルがアップロードされない**: ファイルがWAV形式でサイズ制限（100MB）以下であることを確認
- **処理エラー**: ブラウザコンソールでエラーメッセージを確認
- **CORS問題**: CORSエラーが発生している場合は、以下を確認してください:
  - Lambda関数が正しいCORSヘッダーを返していること
  - API GatewayでCORSが有効になっていること
  - CloudFrontディストリビューションが適切に設定されていること
  - `cdk deploy`を再度実行して設定を更新してみてください
- **要約が表示されない**: 大きなファイルの処理には数分かかる場合があります。5分後も要約が表示されない場合は、ページを更新して要約ステータスを再度確認してください
- **API Gatewayエラー**: フロントエンドのconfig.jsファイルでAPI Gatewayエンドポイントが正しく設定されていることを確認
- **デプロイの失敗**: 詳細なエラーメッセージについてAWSコンソールのCloudFormationを確認

詳細なデプロイ手順とアーキテクチャ情報については、以下を参照してください:
- [Frontend README](frontend-ui/README.md)
- [Backend CDK README](backend-cdk/README.md)

## 開発

### ローカル開発

1. フロントエンドの起動:
```bash
cd frontend-ui
npm install
npm start
```

2. フロントエンドは自動的に以下を使用します:
- 開発用のローカルAPI（http://localhost:3000）
- 本番用のデプロイされたAPIエンドポイント

## 補完ツール

### ユーティリティスクリプト

`utils/`ディレクトリには、UI機能を補完するサポートスクリプトが含まれています:

1. **音声変換ユーティリティ** (`utils/convert_audio.py`):
   ```bash
   # MP4ファイルをWAV形式に変換
   python utils/convert_audio.py --input video.mp4 --output audio.wav

   # 変換した音声をS3にアップロード
   python utils/convert_audio.py --input audio.wav --upload --bucket YOUR_BUCKET_NAME
   ```
   このユーティリティは、ソースファイルを変換する必要がある場合に音声ファイルを準備するのに役立ちます。

2. **PII編集ユーティリティ** (`utils/pii_redaction_utility.py`):
   ```bash
   # サンプルテキストでPII編集をテスト
   python utils/pii_redaction_utility.py --text "My name is John Doe and my phone is 555-123-4567"

   # トランスクリプトファイルを処理
   python utils/pii_redaction_utility.py --file transcript.txt --output redacted.txt
   ```
   これにより、メインのUIフローとは別にPII編集をテストし、編集パターンを検証できます。

### テストスクリプト

`tests/`ディレクトリには、システムのさまざまなコンポーネントをテストするためのスクリプトが含まれています:

1. **Bedrock Guardrailテスト** (`tests/test_lambda_guardrail.py`):
   ```bash
   # サンプルテキストでguardrailをテスト
   python tests/test_lambda_guardrail.py --source OUTPUT
   ```
   Bedrock guardrailがPII編集のために適切に設定されていることを検証します。

2. **電話番号編集テスト** (`tests/test_phone_redaction.py`):
   ```bash
   # さまざまな形式で電話番号の編集をテスト
   python tests/test_phone_redaction.py \
     --guardrail-id YOUR_GUARDRAIL_ARN \
     --region us-east-1 \
     --version DRAFT
   ```
   設定されたBedrock guardrailを使用してすべての電話番号形式が適切に編集されることを確認します。

3. **Step Functionテスト** (`tests/test_step_function.py`):
   ```bash
   # 独自の音声ファイルでAWS Step Functionの実行をテスト
   python tests/test_step_function.py \
     --file YOUR_AUDIO_FILE.wav \
     --region us-west-1 \
     --state-machine VoiceProcessingStateMachine \
     --upload-bucket YOUR_UPLOAD_BUCKET_NAME
   ```
   UIとは独立してバックエンド処理ワークフロー全体をテストします。

   > **重要**: テスト用に独自の音声ファイルを提供し、独自のAWSリソースを指定する必要があります。このリポジトリにはサンプルファイルやハードコードされたAWSリソース識別子は含まれていません。

### UIフローとの統合

これらのツールは、以下の方法でUIを補完します:

- **前処理**: アップロード前にファイルを準備するために変換ユーティリティを使用
- **品質保証**: 本番環境にデプロイする前にPII編集を確認
- **トラブルシューティング**: 問題が発生した場合に特定のコンポーネントを分離してテスト
- **バッチ処理**: 一括操作のためにUI外で複数のファイルを処理

## クイックスタートガイド

アプリケーションを迅速に実行するには、次の手順に従ってください:

### 前提条件

- Node.js 18.x以降
- AWS CLIがインストールされ設定されていること
- AWS CDK CLIがインストールされていること（`npm install -g aws-cdk`）
- TypeScript（`npm install -g typescript`）
- ユーティリティおよびテストスクリプト用のPython 3.8以上
- リソースを作成する権限を持つAWSアカウント
- アカウントでAWS Bedrockアクセスが有効になっていること

### 初回セットアップ

1. **リポジトリのクローン**

   ```bash
   git clone https://github.com/yourusername/sample-bedrock-whisper-pii-audio-summarizer.git
   cd sample-bedrock-whisper-pii-audio-summarizer
   ```

2. **AWS認証情報の設定**

   AWS認証情報が適切に設定されていることを確認します:
   ```bash
   aws configure
   ```
   AWSアクセスキーID、シークレットアクセスキー、デフォルトリージョン（例: us-west-1）、出力形式（json）を入力します。

3. **必要な環境ファイルの作成**

   フロントエンド用:
   ```bash
   # frontend-uiディレクトリに.envファイルを作成
   cat > frontend-ui/.env << EOL
   REACT_APP_API_ENDPOINT=http://localhost:3000/dev
   REACT_APP_REGION=us-east-1
   REACT_APP_UPLOAD_BUCKET=frontend-uploads-dev
   REACT_APP_SUMMARIES_BUCKET=frontend-summaries-dev
   EOL
   ```

   > 注意: バックエンドをデプロイした後、これらの値を実際のAWSリソースに置き換えます。

4. **AWS Bedrock Guardrailの作成**

   - PII編集を設定するには、[AWS Bedrock Guardrail作成手順](backend-cdk/README.md#creating-bedrock-guardrails)に従ってください。

### バックエンドのデプロイ

```bash
# バックエンドディレクトリに移動
cd backend-cdk

# 依存関係のインストール
npm install

# モジュール解決の問題を回避するためにTypeScript依存関係をローカルにインストール
npm install typescript ts-node @types/node

# AWSアカウントでCDKをブートストラップ
cdk bootstrap aws://$(aws sts get-caller-identity --query 'Account' --output text)/$(aws configure get region)

# テンプレートを合成して作成されるリソースを確認（オプション）
npx cdk synth

# スタックをデプロイ
npx cdk deploy
```

> **S3バケット命名に関する注意**: CDKコードは、バケットプレフィックスとして「genaicapstone-」または「frontend-」のいずれかを使用する場合があります。新規ユーザーとして、どちらの命名規則も使用できます - フロントエンド設定がCDKデプロイから出力されたバケット名と一致していることを確認してください。

デプロイが完了したら、以下の出力をメモしてください:
- API Gateway URL
- CloudFrontディストリビューションURL
- S3バケット名

### フロントエンドの設定と実行

```bash
# フロントエンドディレクトリに移動
cd ../frontend-ui

# 依存関係のインストール
npm install

# CDK出力からの値で.envファイルを更新
# 実際のエンドポイントでfrontend-ui/.envを編集

# フロントエンドを起動
npm start
```

### インストールの確認

1. ブラウザで`http://localhost:3000`を開く
2. 音声ファイル（.mp3、.wav、.mp4）をアップロード
3. ファイルが処理され、要約が表示されるはずです

### トラブルシューティング

- **CDKデプロイエラー**: 適切なAWS権限があり、アカウントでAWS Bedrockが有効になっていることを確認してください。
- **フロントエンド接続の問題**: .envファイルのAPI Gateway URLがCDK出力と一致していることを確認してください。
- **処理エラー**: Lambda関数のCloudWatchログを確認して問題を特定してください。

より詳細な設定オプションについては、[backend README](backend-cdk/README.md)と[frontend README](frontend-ui/README.md)を参照してください。
