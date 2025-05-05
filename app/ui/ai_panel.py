import sys
import logging
from app.services.rule_service import RuleService
import os, json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QGroupBox, QToolButton, QFrame, QToolTip, QMenu)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AIPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初期ルール状態とJSONからの履歴ルールの設定
        self.current_rule = None
        self.rule_service = RuleService()
        self.load_rules_from_json()
        self.setup_ui()
        
    def setup_ui(self):
        """AIパネルのUI設定"""
        # レイアウト設定
        self.setStyleSheet("background-color: #F5F5F5; color: #000000;")
        ai_layout = QVBoxLayout(self)
        ai_layout.setContentsMargins(15, 15, 15, 15)
        ai_layout.setSpacing(15)  # 均等な余白
        
        # AIパネルタイトルとボタンを含む上部レイアウト
        top_layout = QHBoxLayout()
        
        # AIパネルタイトル（左上に配置）
        ai_title = QLabel("AI_panel")
        ai_title.setFont(QFont("Arial", 14, QFont.Bold))
        ai_title.setStyleSheet("color: #000000;")
        top_layout.addWidget(ai_title)
        
        # 右側にスペースを追加
        top_layout.addStretch()
        
        # 履歴ボタン（右上に配置）
        self.history_btn = QToolButton()
        self.history_btn.setText("📋 履歴")
        self.history_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.history_btn.setStyleSheet("color: #000000; background-color: transparent;")
        self.history_btn.setToolTip("過去の履歴からルールを適用します")
        top_layout.addWidget(self.history_btn)
        # ヒストリールールメニュー設定（モック）
        menu = QMenu(self)
        for rule in self.history_rules:
            action = menu.addAction(rule)
            action.triggered.connect(lambda checked, r=rule: self.apply_history_rule(r))
        self.history_btn.setMenu(menu)
        self.history_btn.setPopupMode(QToolButton.InstantPopup)
        # 上部レイアウトをパネルに追加
        ai_layout.addLayout(top_layout)
        
        # 処理ルール表示フレーム
        rule_frame = QFrame()
        rule_frame.setFrameShape(QFrame.StyledPanel)
        rule_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #DDDDDD;")
        rule_layout = QVBoxLayout(rule_frame)
        
        # 処理ルールのタイトル
        rule_title = QLabel("処理ルール")
        rule_title.setFont(QFont("Arial", 12, QFont.Bold))
        rule_title.setStyleSheet("color: #000000;")
        rule_layout.addWidget(rule_title)
        
        # ルール内容 - 左寄せにして大きいフォントに変更
        self.rule_content = QLabel("ルール未作成")
        self.rule_content.setAlignment(Qt.AlignLeft)  # 左寄せに変更
        self.rule_content.setFont(QFont("Arial", 14))  # フォントサイズを14に変更
        self.rule_content.setStyleSheet("color: #000000; padding: 10px;")
        rule_layout.addWidget(self.rule_content)
        
        # ルール内ボタンレイアウト
        rule_buttons_layout = QHBoxLayout()
        
        # 自動生成ボタン
        self.auto_generate_btn = QPushButton("サンプルから生成")
        self.auto_generate_btn.setStyleSheet(
            "background-color: #4F94EF; color: white; font-size: 12px; font-weight: bold; padding: 5px;"
        )
        self.auto_generate_btn.setToolTip("AIがサンプルを解析してルールを自動生成")
        rule_buttons_layout.addWidget(self.auto_generate_btn)
        
        # ルール詳細ボタン
        self.rule_detail_btn = QPushButton("ルール詳細を編集")
        self.rule_detail_btn.setStyleSheet(
            "background-color: #F0F0F0; color: #000000; font-size: 12px; padding: 5px; border: 1px solid #CCCCCC;"
        )
        self.rule_detail_btn.setToolTip("ルールの詳細設定を表示します")
        rule_buttons_layout.addWidget(self.rule_detail_btn)
        
        # ボタンレイアウトをルールフレームに追加
        rule_layout.addLayout(rule_buttons_layout)
        
        # ルールフレームをパネルに追加
        ai_layout.addWidget(rule_frame)
        
        # 処理ボタンのグループ化（QFrameに変更）
        process_frame = QFrame()
        process_frame.setFrameShape(QFrame.StyledPanel)
        process_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #DDDDDD;")
        process_layout = QVBoxLayout(process_frame)
        process_layout.setContentsMargins(10, 10, 10, 10)
        process_layout.setSpacing(10)
        
        # 処理ルール実行のタイトル（処理ルールのタイトルと同じスタイル）
        process_title = QLabel("処理ルールを実行する")
        process_title.setFont(QFont("Arial", 12, QFont.Bold))
        process_title.setStyleSheet("color: #000000;")
        process_layout.addWidget(process_title)
        
        # 処理ボタン
        self.process_selected_btn = QPushButton("選択行だけ処理")
        self.process_all_btn = QPushButton("未処理を一括処理")
        
        # ボタンスタイル
        button_style = "padding: 5px; background-color: #F0F0F0; color: #000000; border: 1px solid #CCCCCC;"
        self.process_selected_btn.setStyleSheet(button_style)
        self.process_all_btn.setStyleSheet(button_style)
        
        process_layout.addWidget(self.process_selected_btn)
        process_layout.addWidget(self.process_all_btn)
        
        ai_layout.addWidget(process_frame)
        
        # 下部の余白を追加
        ai_layout.addStretch()
        
        # イベント接続
        # JSON の最初のルールを適用する
        try:
            self.auto_generate_btn.clicked.disconnect()
        except Exception:
            pass
        self.auto_generate_btn.clicked.connect(self.on_auto_generate)
        self.rule_detail_btn.clicked.connect(self.show_rule_detail_tooltip)
        # 初期UI状態の更新
        self.update_ui_state()
    
    def show_auto_generate_message(self):
        """自動生成ボタン押下時の動作"""
        QToolTip.showText(self.auto_generate_btn.mapToGlobal(self.auto_generate_btn.rect().center()), 
                        "自動生成実行中...", self)
    
    def show_rule_detail_tooltip(self):
        """ルール詳細ボタン押下時の動作"""
        QToolTip.showText(self.rule_detail_btn.mapToGlobal(self.rule_detail_btn.rect().center()), 
                        "ルールの詳細設定画面を開きます", self)
    
    def update_ui_state(self):
        """UI要素を現在のルール状態に応じて更新"""
        if self.current_rule is None:
            logger.debug("現在のルールなし、UIを更新します")
            self.rule_content.setText("ルール未作成")
            # 詳細編集ボタンは非表示にする
            self.rule_detail_btn.hide()
            # サンプル生成ボタンはデフォルト文言に戻す
            self.auto_generate_btn.setText("サンプルから生成")
            self.process_selected_btn.setEnabled(False)
            self.process_all_btn.setEnabled(False)
            # 処理ボタンを無効化し、灰色表示
            self.process_selected_btn.setStyleSheet("padding: 5px; background-color: #E0E0E0; color: #A0A0A0; border: 1px solid #CCCCCC;")
            self.process_all_btn.setStyleSheet("padding: 5px; background-color: #E0E0E0; color: #A0A0A0; border: 1px solid #CCCCCC;")
            logger.debug("処理ボタンを無効化しました")
        else:
            logger.debug(f"ルール'{self.current_rule}'適用、UIを更新します")
            self.rule_content.setText(self.current_rule)
            # 詳細編集ボタンを表示
            self.rule_detail_btn.show()
            # サンプル生成ボタンの文言を変更
            self.auto_generate_btn.setText("再生成する")
            self.process_selected_btn.setEnabled(True)
            self.process_all_btn.setEnabled(True)
            # 処理ボタンを有効化し、色付き表示
            self.process_selected_btn.setStyleSheet("padding: 5px; background-color: #4F94EF; color: white; border: 1px solid #4F94EF;")
            self.process_all_btn.setStyleSheet("padding: 5px; background-color: #4F94EF; color: white; border: 1px solid #4F94EF;")
            logger.debug("処理ボタンを有効化しました")

    def apply_history_rule(self, rule):
        """履歴から選択したルールを適用"""
        logger.debug(f"apply_history_rule called with rule: {rule}")
        self.current_rule = rule
        self.update_ui_state()
        QToolTip.showText(self.history_btn.mapToGlobal(self.history_btn.rect().center()), 
                          f"ルール「{rule}」を適用しました", self)
        # 選択ルールデータの確認
        rule_data = self.rule_map.get(rule)
        logger.debug(f"rule_data from rule_map: {rule_data}")
        # サンプルデータをロードしてExcelパネルに反映
        if rule_data:
            if hasattr(self, 'excel_panel'):
                sample_data = rule_data.get('sample_data', {})
                logger.debug(f"loading sample_data into excel_panel: {sample_data}")
                try:
                    self.excel_panel.load_sample_data(sample_data)
                except Exception as e:
                    logger.error(f"サンプルデータロードエラー: {e}")
            else:
                logger.error("excel_panel 属性がありません。IntegratedExcelUIでの参照設定を確認してください。")

    def load_rules_from_json(self):
        """ルール管理サービスからルールを読み込む"""
        # サービスからルール一覧を取得
        try:
            self.rules_data = self.rule_service.get_rules()
        except Exception as e:
            logger.error(f"ルール取得エラー: {e}")
            self.rules_data = []
        # ルールタイトルのリストとマッピングを作成
        self.history_rules = [r.get('title', '') for r in self.rules_data]
        self.rule_map = {r.get('title', ''): r for r in self.rules_data}
        logger.debug(f"rules_data loaded: {self.rules_data}")
        logger.debug(f"history_rules keys: {self.history_rules}")

    def on_auto_generate(self):
        """自動生成ボタンで新規ルールを生成し適用"""
        # 処理中メッセージ表示
        self.show_auto_generate_message()
        # サンプルデータ取得
        samples = []
        table = self.excel_panel.sample_table
        # ヘッダー取得（Noneの場合は空文字を設定）
        headers = []
        for c in range(table.columnCount()):
            item = table.item(0, c)
            headers.append(item.text() if item else "")
        logger.debug(f"Auto-generate headers: {headers}")
        for row in range(1, table.rowCount()):
            logger.debug(f"Processing sample row {row}")
            input_item = table.item(row, 1)
            if not input_item:
                logger.warning(f"Row {row}: input_item is None")
                continue
            if not input_item.text():
                logger.debug(f"Row {row}: input text empty, skip")
                continue
            output = {}
            for col, header in enumerate(headers[2:], start=2):
                item = table.item(row, col)
                if not item:
                    logger.debug(f"Row {row}, col {col} header '{header}': item is None")
                text = item.text() if item else ''
                output[header] = text
            samples.append({'input': input_item.text(), 'output': output, 'fields': headers[2:]})
        # ルール生成または再生成API呼び出し
        try:
            if self.current_rule is None:
                # 新規ルール作成
                metadata = self.rule_service.create_rule(samples)
            else:
                # 既存ルール再生成
                metadata = self.rule_service.regenerate_rule(self.current_rule, samples)
            new_title = metadata.get('rule_name')
            # UIにルール追加または更新
            if new_title not in self.history_rules:
                self.rules_data.append(metadata)
                self.history_rules.append(new_title)
                self.rule_map[new_title] = metadata
                action = self.history_btn.menu().addAction(new_title)
                action.triggered.connect(lambda _, r=new_title: self.apply_history_rule(r))
            # 過去のルールを削除してUIからも消す（再生成時）
            if self.current_rule and self.current_rule != new_title:
                # remove old action
                for act in self.history_btn.menu().actions():
                    if act.text() == self.current_rule:
                        self.history_btn.menu().removeAction(act)
                        break
            # ルール適用
            self.apply_history_rule(new_title)
        except NotImplementedError:
            logger.error("create_rule未実装")
            QToolTip.showText(self.auto_generate_btn.mapToGlobal(self.auto_generate_btn.rect().center()),
                              "ルール生成機能が未実装です", self)
        except Exception as e:
            logger.error(f"ルール生成エラー: {e}")
            QToolTip.showText(self.auto_generate_btn.mapToGlobal(self.auto_generate_btn.rect().center()),
                              f"ルール生成中にエラーが発生しました: {e}", self)