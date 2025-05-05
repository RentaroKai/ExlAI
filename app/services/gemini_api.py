import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Iterator
import json
import time
import httplib2

from google import genai
from google.genai import types
from utils.config import config_manager

logger = logging.getLogger(__name__)

# デフォルトのモデル設定 (環境または設定未指定時のフォールバック)
DEFAULT_TRANSCRIPTION_MODEL = config_manager.get_model("gemini_transcription") or "gemini-2.0-flash-001"
DEFAULT_MINUTES_MODEL = config_manager.get_model("gemini_minutes") or "gemini-2.0-flash-001"
DEFAULT_TITLE_MODEL = config_manager.get_model("gemini_title") or "gemini-2.0-flash-001"

MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒
MAX_FILE_SIZE_MB = 100  # デフォルトの最大ファイルサイズ（MB）
MAX_FILE_WAIT_RETRIES = 30  # ファイル処理待機の最大リトライ回数
FILE_WAIT_RETRY_DELAY = 5  # ファイル処理待機の間隔（秒）

class MediaType:
    """サポートされるメディアタイプの定数"""
    AUDIO = "audio"
    VIDEO = "video"

class GeminiAPIError(Exception):
    """Gemini API処理中のエラーを表すカスタム例外"""
    pass

# 互換性のために既存の例外クラス名も保持
TranscriptionError = GeminiAPIError

class VideoFileTooLargeError(GeminiAPIError):
    """動画ファイルサイズが大きすぎる場合のエラー"""
    pass

class GeminiAPI:
    """Gemini APIクライアント"""
    
    def __init__(
        self,
        transcription_model: str = None,
        minutes_model: str = None,
        title_model: str = None,
        max_file_size_mb: int = None,
        api_key: str = None
    ):
        """Gemini APIクライアントを初期化
        
        Args:
            transcription_model (str, optional): 書き起こし用のモデル名
            minutes_model (str, optional): 議事録まとめ用のモデル名
            title_model (str, optional): タイトル生成用のモデル名
            max_file_size_mb (int, optional): 最大ファイルサイズ（MB）
            api_key (str, optional): 直接指定するAPIキー
        """
        # SSL証明書の設定（互換性のため）
        cert_path = os.environ.get('SSL_CERT_FILE')
        if cert_path:
            httplib2.CA_CERTS = cert_path
            logger.info(f"SSL証明書が設定されました: {cert_path}")
            
        # 設定の読み込み
        config = config_manager.get_config()
        
        # APIキーを取得（優先順位: 引数 > 環境変数 > 設定ファイル）
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or config.get('gemini_api_key')
        
        if not self.api_key:
            error_msg = "Gemini API keyが設定されていません。環境変数GEMINI_API_KEY、GOOGLE_API_KEY、または設定ファイルのgemini_api_keyを設定してください。"
            logger.error(error_msg)
            raise GeminiAPIError(error_msg)
        
        # モデル名の設定（引数 → 設定ファイル → デフォルト値の優先順）
        self.transcription_model = transcription_model or config.get('models', {}).get('gemini_transcription', DEFAULT_TRANSCRIPTION_MODEL)
        self.minutes_model = minutes_model or config.get('models', {}).get('gemini_minutes', DEFAULT_MINUTES_MODEL)
        self.title_model = title_model or config.get('models', {}).get('gemini_title', DEFAULT_TITLE_MODEL)
        
        # 最大ファイルサイズの設定
        self.max_file_size_mb = max_file_size_mb or config.get('max_file_size_mb', MAX_FILE_SIZE_MB)
        
        # クライアントの初期化 - Gemini API 新しいスタイル
        # APIバージョンをv1alphaに設定
        self.client = genai.Client(
            api_key=self.api_key,
            http_options={'api_version': 'v1alpha'}
        )
        
        # 互換性のための設定
        self.generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }
        
        # タイトル生成用の設定
        self.title_generation_config = {
            "temperature": 1.0,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 100,
            "response_mime_type": "application/json",
        }
        
        # 議事録生成用の設定
        self.minutes_generation_config = {
            "temperature": 1.0,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        
        # システムプロンプト（互換性のため）
        self.system_prompt = """あなたは会議の書き起こしを行う専門家です。
    以下の点に注意して、音声ファイルに忠実な書き起こしテキストを作成してください：
    1. 与えられたビデオから発言者を特定する
    2. 発言者と発言内容を分けて表示
    3. 発言の整形は最小限にとどめ、発言をそのまま書き起こす
    4. 以下のJSON形式で出力：
    {
      "conversations": [
        {
          "speaker": "発言者名",
          "utterance": "発言内容"
        },
        ...
      ]
    }
    
    入力された音声の書き起こしテキストを上記の形式に変換してください。 。"""
        
        # タイトル生成用のシステムプロンプト
        self.title_system_prompt = """会議の書き起こしからこの会議のメインとなる議題が何だったのかを教えて。例：取引先とカフェの方向性に関する会議"""
        
        logger.info(f"GeminiAPI initialized - Transcription model: {self.transcription_model}")
        logger.info(f"Minutes model: {self.minutes_model}, Title model: {self.title_model}")
        logger.info(f"Max file size: {self.max_file_size_mb} MB")

    def _check_file_size(self, file_path: str) -> None:
        """ファイルサイズをチェックし、大きすぎる場合は例外を発生
        
        Args:
            file_path (str): チェックするファイルのパス
            
        Raises:
            VideoFileTooLargeError: ファイルサイズが制限を超えている場合
            FileNotFoundError: ファイルが存在しない場合
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
        
        file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise VideoFileTooLargeError(
                f"ファイルサイズ({file_size_mb:.1f}MB)が制限({self.max_file_size_mb}MB)を超えています。"
                "ファイルを小さく分割するか、設定の'max_file_size_mb'を増やしてください。"
            )

    def upload_file(self, file_path: str, mime_type: Optional[str] = None) -> Any:
        """ファイルをGemini APIにアップロード
        
        Args:
            file_path (str): アップロードするファイルのパス
            mime_type (str, optional): ファイルのMIMEタイプ (非推奨、新APIでは自動検出)
            
        Returns:
            Any: アップロードされたファイルオブジェクト
            
        Raises:
            GeminiAPIError: アップロードに失敗した場合
        """
        try:
            # ファイルサイズのチェック
            self._check_file_size(file_path)
            
            # ファイルをアップロード
            logger.info(f"Uploading file: {file_path}")
            uploaded_file = self.client.files.upload(file=file_path)
            logger.info(f"File uploaded successfully: {uploaded_file.uri}")
            
            # ファイル処理の完了を待機（ACTIVE状態になるまで）
            if not self.wait_for_processing(uploaded_file):
                raise GeminiAPIError("ファイルの処理が完了しませんでした")
            
            return uploaded_file
        except VideoFileTooLargeError:
            raise
        except Exception as e:
            error_msg = f"ファイルのアップロードに失敗しました: {str(e)}"
            logger.error(error_msg)
            raise GeminiAPIError(error_msg)

    def wait_for_processing(self, file) -> bool:
        """ファイルの処理完了を待機"""
        for attempt in range(MAX_FILE_WAIT_RETRIES):
            status = self.client.files.get(file.uri).state
            logger.info(f"File processing status: {status}")
            if status == types.File.State.ACTIVE:
                return True
            time.sleep(FILE_WAIT_RETRY_DELAY)
        return False

    def transcribe(
        self,
        file_path: str,
        media_type: str = MediaType.AUDIO,
        stream: bool = False
    ) -> Union[str, Iterator[str]]:
        """音声/動画の書き起こしを行う"""
        # ファイルアップロード
        uploaded = self.upload_file(file_path)
        contents = []
        # ストリーミング or ノーマル
        if stream:
            return self._transcribe_stream(contents, self.generation_config)
        else:
            return self._transcribe_normal(contents, self.generation_config)

    def _transcribe_stream(self, contents: List, config: Dict) -> Iterator[str]:
        """ストリーミング書き起こし (未実装)"""
        raise NotImplementedError("Streaming transcription is not implemented")

    def _transcribe_normal(self, contents: List, config: Dict) -> str:
        """ノーマル書き起こし (未実装)"""
        raise NotImplementedError("Normal transcription is not implemented")

    def generate_title(self, transcription_text: str) -> str:
        """タイトルを生成する"""
        # 新しいAPIを使用してタイトルを生成
        try:
            response = self.client.models.generate_content(
                model=self.title_model,
                contents=transcription_text
            )
            text = response.text
            try:
                data = json.loads(text)
                return data.get("title", text)
            except json.JSONDecodeError:
                logger.warning("タイトル生成レスポンスのJSON解析に失敗、元テキストを返します")
                return text
        except Exception as e:
            logger.error(f"タイトル生成エラー: {e}")
            return ""

    def summarize_minutes(self, text: str, system_prompt: str = None) -> str:
        """議事録を要約する"""
        # 新しいAPIを使用して議事録要約を生成
        prompt_text = system_prompt or self.system_prompt
        try:
            response = self.client.models.generate_content(
                model=self.minutes_model,
                contents=prompt_text
            )
            return response.text
        except Exception as e:
            logger.error(f"議事録要約エラー: {e}")
            return "" 