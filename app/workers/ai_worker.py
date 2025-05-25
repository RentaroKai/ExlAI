# -*- coding: utf-8 -*-
"""
AI処理用ワーカースレッド
"""

import logging
import asyncio
from PySide6.QtCore import QThread, Signal
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class AIWorker(QThread):
    """AI処理を別スレッドで実行するワーカークラス"""
    
    # シグナル定義
    finished = Signal(list)      # 処理完了時に結果リストを送信
    error_occurred = Signal(str) # エラー発生時にエラーメッセージを送信
    
    def __init__(self, rule_service, rule_id: int, inputs: List[str]):
        """
        Args:
            rule_service: RuleServiceのインスタンス
            rule_id: 適用するルールのID
            inputs: 処理対象の入力データリスト
        """
        super().__init__()
        self.rule_service = rule_service
        self.rule_id = rule_id
        self.inputs = inputs
        
    def run(self):
        """別スレッドで実行されるメイン処理"""
        try:
            logger.info(f"AIWorker開始: rule_id={self.rule_id}, 対象行数={len(self.inputs)}件")
            
            # AI処理実行（非同期メソッドをasyncio.run()で呼び出し）
            results = asyncio.run(self.rule_service.apply_rule(self.rule_id, self.inputs))
            
            logger.info(f"AIWorker完了: 結果件数={len(results)}件")
            
            # 成功時のシグナル送信
            self.finished.emit(results)
            
        except Exception as e:
            logger.error(f"AIWorker エラー: {e}")
            # エラー時のシグナル送信
            self.error_occurred.emit(str(e))


class RuleCreationWorker(QThread):
    """ルール作成・再生成を別スレッドで実行するワーカークラス"""
    
    # シグナル定義
    finished = Signal(dict)      # 処理完了時にルールメタデータを送信
    error_occurred = Signal(str) # エラー発生時にエラーメッセージを送信
    
    def __init__(self, rule_service, samples: List[Dict[str, Any]], mode: str, rule_id: int = None):
        """
        Args:
            rule_service: RuleServiceのインスタンス
            samples: サンプルデータのリスト
            mode: 処理モード
            rule_id: 再生成の場合のルールID（新規作成の場合はNone）
        """
        super().__init__()
        self.rule_service = rule_service
        self.samples = samples
        self.mode = mode
        self.rule_id = rule_id
        
    def run(self):
        """別スレッドで実行されるメイン処理"""
        try:
            if self.rule_id is None:
                logger.info(f"RuleCreationWorker開始: 新規作成 mode={self.mode}, サンプル数={len(self.samples)}件")
                # 新規作成
                result = asyncio.run(self.rule_service.create_rule(self.samples, self.mode))
            else:
                logger.info(f"RuleCreationWorker開始: 再生成 rule_id={self.rule_id}, mode={self.mode}, サンプル数={len(self.samples)}件")
                # 再生成
                result = asyncio.run(self.rule_service.regenerate_rule(self.rule_id, self.samples, self.mode))
            
            logger.info(f"RuleCreationWorker完了: result={result}")
            
            # 成功時のシグナル送信
            self.finished.emit(result)
            
        except Exception as e:
            logger.error(f"RuleCreationWorker エラー: {e}")
            # エラー時のシグナル送信
            self.error_occurred.emit(str(e)) 