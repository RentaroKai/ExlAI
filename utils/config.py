import os
import json
import logging
import sys
import shutil

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    設定ファイル（JSON/YAML）を読み込み、モデル名や各種設定を提供するシングルトンマネージャ
    """
    _instance = None

    def __new__(cls, config_path=None):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path=None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        # exe一体化環境での設定ファイル永続化
        if getattr(sys, 'frozen', False):
            exec_dir = os.path.dirname(sys.executable)
            # パッケージ内に埋め込まれているconfig.json
            packaged_config = os.path.join(sys._MEIPASS, 'config.json')
            # 実行ファイルフォルダへの永続化パス
            persistent_config = os.path.join(exec_dir, 'config.json')
            if not os.path.exists(persistent_config):
                try:
                    shutil.copy(packaged_config, persistent_config)
                    logger.info(f"Copied default config to {persistent_config}")
                except Exception as e:
                    logger.error(f"Failed to copy default config.json: {e}")
            self.config_path = persistent_config
        else:
            # 通常実行時はプロジェクトルートのconfig.jsonを利用
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            self.config_path = config_path or os.path.join(base_dir, 'config.json')
        self._config = {}
        self._load_config()

    def _load_config(self):
        """設定ファイルを読み込む"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.debug(f"Loaded config from {self.config_path}")
        except FileNotFoundError:
            logger.warning(f"Config file not found at {self.config_path}, using defaults")
            self._config = {}
        except json.JSONDecodeError as e:
            logger.error(f"Config JSON decode error: {e}")
            self._config = {}

    def get_config(self):
        """全設定を返却する"""
        return self._config

    def get_model(self, key: str):
        """
        指定したモデル名設定を返却する。
        設定ファイルの 'models' セクション、または環境変数から取得。
        key: 設定ファイル/modelセクションおよび環境変数のキー名
        """
        # 設定ファイルから取得
        models = self._config.get('models', {})
        if key in models:
            return models[key]
        # 環境変数から取得 (大文字化)
        env_key = key.upper()
        env_val = os.getenv(env_key)
        if env_val:
            logger.debug(f"Loaded model {key} from ENV {env_key}")
            return env_val
        logger.error(f"Model {key} not found in config or environment variable {env_key}")
        return None

    def save_config(self):
        """現在の設定をファイルに保存する"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Config save error: {e}")

# モジュールレベルでインスタンスを生成
config_manager = ConfigManager() 