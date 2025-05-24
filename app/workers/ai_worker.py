# -*- coding: utf-8 -*-
"""
AI処理用ワーカースレッド
"""

import logging
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
            
            # AI処理実行
            results = self.rule_service.apply_rule(self.rule_id, self.inputs)
            
            logger.info(f"AIWorker完了: 結果件数={len(results)}件")
            
            # 成功時のシグナル送信
            self.finished.emit(results)
            
        except Exception as e:
            logger.error(f"AIWorker エラー: {e}")
            # エラー時のシグナル送信
            self.error_occurred.emit(str(e)) 