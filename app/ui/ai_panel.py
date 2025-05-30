import sys
import logging
from app.services.rule_service import RuleService, ProcessMode
from app.workers.ai_worker import RuleCreationWorker
import os, json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QGroupBox, QToolButton, QFrame, QToolTip, QMenu, QDialog, QMessageBox)
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from app.ui.rule_edit_dialog import RuleEditDialog

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AIPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初期ルール状態とJSONからの履歴ルールの設定
        self.current_rule_id = None
        self.current_mode = ProcessMode.NORMAL  # 現在のモード
        # ルール作成モードの状態管理を追加
        self.is_new_rule_mode = True  # True: 新規作成モード, False: 履歴選択モード
        self.rule_service = RuleService()
        self.load_rules_from_json()
        self.setup_ui()
        
    def setup_ui(self):
        """AIパネルのUI設定"""
        # レイアウト設定とモダンなスクロールバー
        self.setStyleSheet("""
            QWidget {
                background-color: #333333; 
                color: #FFFFFF;
            }
            
            /* 🎨 AIパネル用モダンスクロールバー */
            QScrollArea QScrollBar:vertical {
                background-color: transparent;
                width: 8px;
                border: none;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollArea QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.0);
                border-radius: 4px;
                min-height: 20px;
                margin: 2px;
            }
            QScrollArea QScrollBar::handle:vertical:hover {
                background-color: rgba(255, 255, 255, 0.4);
            }
            QScrollArea QScrollBar::handle:vertical:pressed {
                background-color: rgba(255, 255, 255, 0.6);
            }
            QScrollArea QScrollBar::add-line:vertical,
            QScrollArea QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollArea QScrollBar::add-page:vertical,
            QScrollArea QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollArea:hover QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)  # 背景色をダークグレーに変更
        ai_layout = QVBoxLayout(self)
        ai_layout.setContentsMargins(5, 5, 5, 15)
        ai_layout.setSpacing(5)  # 均等な余白
        
        # AIパネルタイトルとボタンを含む上部レイアウト
        top_layout = QHBoxLayout()
        
        # AIパネルタイトル（左上に配置）
        ai_title = QLabel("AI_panel")
        ai_title.setFont(QFont("Arial", 12, QFont.Bold))
        ai_title.setStyleSheet("color: #3A506B;")  # テンプレートラベルと同じ色
        top_layout.addWidget(ai_title)
        ai_title.hide()
        
        # 右側にスペースを追加
        top_layout.addStretch()
        
        # 履歴ボタンを処理ルール枠内に表示
        history_layout = QHBoxLayout()
        history_layout.addStretch()
        
        # 新規作成ボタン（左側）
        self.new_rule_btn = QPushButton("リセット")
        self.new_rule_btn.setFixedHeight(30)
        self.new_rule_btn.setToolTip("テンプレートから新しいルールを作成します")
        history_layout.addWidget(self.new_rule_btn)
        
        # 履歴ボタン（右側）
        self.history_btn = QToolButton()
        self.history_btn.setText("📋 履歴")
        self.history_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.history_btn.setStyleSheet("color: #3A506B; background-color: transparent; border: none;")
        self.history_btn.setToolTip("過去の履歴からルールを適用します")
        self.history_btn.setFixedHeight(30)
        history_layout.addWidget(self.history_btn)
        # ヒストリールールメニュー設定（IDベース）
        self.create_history_menu()
        
        # 処理ルール表示フレーム
        rule_frame = QFrame()
        rule_frame.setFrameShape(QFrame.StyledPanel)
        rule_frame.setStyleSheet("background-color: #FFFFFF; border: none;")  # 枠線を非表示にする
        rule_layout = QVBoxLayout(rule_frame)
        # rule_layoutのマージンとスペーシングを統一
        rule_layout.setContentsMargins(10, 10, 10, 10)
        rule_layout.setSpacing(10)
        
        # 履歴ボタンを処理ルール枠内に表示
        rule_layout.addLayout(history_layout)
        
        # 処理ルールのタイトル
        rule_title = QLabel("処理ルール")
        rule_title.setFont(QFont("Arial", 12, QFont.Bold))
        rule_title.setStyleSheet("color: #3A506B;")  # タイトル色を統一
        rule_layout.addWidget(rule_title)
        
        # ルール内容 - 左寄せにして大きいフォントに変更
        self.rule_content = QLabel("ルール未作成")
        self.rule_content.setAlignment(Qt.AlignLeft)  # 左寄せに変更
        self.rule_content.setFont(QFont("Arial", 14))  # フォントサイズを14に変更
        # 水平方向の余白をなくし、垂直パディングのみ確保
        self.rule_content.setStyleSheet("color: #333333; padding: 10px 0px;")
        rule_layout.addWidget(self.rule_content)
        
        # ルール名の下にプロンプト用ラベルを追加
        self.prompt_content = QLabel("")
        self.prompt_content.setAlignment(Qt.AlignLeft)
        self.prompt_content.setWordWrap(True)
        self.prompt_content.setFont(QFont("Arial", 10))
        self.prompt_content.setStyleSheet("color: #555555; padding: 5px;")
        self.prompt_content.hide()
        rule_layout.addWidget(self.prompt_content)
        
        # ルール内ボタンレイアウト
        rule_buttons_layout = QHBoxLayout()
        
        # 自動生成ボタン
        self.auto_generate_btn = QPushButton("テンプレートからルール生成")
        self.auto_generate_btn.setStyleSheet(
            "background-color: #4B918B; color: white; font-size: 12px; font-weight: bold; padding: 5px; border-radius: 3px;"  # ティール色に変更
        )
        self.auto_generate_btn.setToolTip("AIがサンプルを解析してルールを自動生成")
        rule_buttons_layout.addWidget(self.auto_generate_btn)
        
        # ルール詳細ボタン
        self.rule_detail_btn = QPushButton("ルール詳細を編集")
        self.rule_detail_btn.setStyleSheet(
            "background-color: #E8EEF4; color: #3A506B; font-size: 12px; padding: 5px; border: 1px solid #D1D9E6; border-radius: 3px;"  # 色を統一
        )
        self.rule_detail_btn.setToolTip("ルールの詳細設定を表示します")
        rule_buttons_layout.addWidget(self.rule_detail_btn)

        # ルール削除ボタン
        self.rule_delete_btn = QPushButton("ルールを削除")
        self.rule_delete_btn.setStyleSheet(
            "background-color: #E74C3C; color: white; font-size: 12px; padding: 5px; border: 1px solid #C0392B; border-radius: 3px;"
        )
        self.rule_delete_btn.setToolTip("選択中のルールを削除します")
        rule_buttons_layout.addWidget(self.rule_delete_btn)
        
        # ボタンレイアウトをルールフレームに追加
        rule_layout.addLayout(rule_buttons_layout)
        
        # ルールフレームをパネルに追加
        ai_layout.addWidget(rule_frame)
        
        # 処理ボタンのグループ化（QFrameに変更）
        process_frame = QFrame()
        process_frame.setFrameShape(QFrame.StyledPanel)
        process_frame.setStyleSheet("background-color: #FFFFFF; border: none;")  # 枠線を非表示にする
        process_layout = QVBoxLayout(process_frame)
        process_layout.setContentsMargins(10, 10, 10, 10)
        process_layout.setSpacing(10)
        
        # 処理ルール実行のタイトル（処理ルールのタイトルと同じスタイル）
        process_title = QLabel("処理ルールを実行する")
        process_title.setFont(QFont("Arial", 12, QFont.Bold))
        process_title.setStyleSheet("color: #3A506B;")  # タイトル色を統一
        process_layout.addWidget(process_title)
        
        # 処理ボタン
        self.process_selected_btn = QPushButton("選択行だけ処理")
        self.process_all_btn = QPushButton("未処理を一括処理")
        
        # ボタンスタイル
        selected_button_style = "padding: 8px; background-color: #4B918B; color: white; border-radius: 3px; font-weight: bold;"  # ティール色に変更
        all_button_style = "padding: 8px; background-color: #4B918B; color: white; border-radius: 3px; font-weight: bold;"  # ティール色
        self.process_selected_btn.setStyleSheet(selected_button_style)
        self.process_all_btn.setStyleSheet(all_button_style)
        
        process_layout.addWidget(self.process_selected_btn)
        process_layout.addWidget(self.process_all_btn)
        
        ai_layout.addWidget(process_frame)
        
        # 下部の余白を追加
        ai_layout.addStretch()
        
        # イベント接続
        # 既存の接続を安全に解除
        try:
            self.auto_generate_btn.clicked.disconnect()
        except (TypeError, RuntimeError, AttributeError):
            # 接続がない場合やオブジェクトが無効な場合のエラーを無視
            pass
        
        # 新しい接続を設定
        self.auto_generate_btn.clicked.connect(self.on_auto_generate)
        self.rule_detail_btn.clicked.connect(self.show_rule_detail_dialog)
        self.rule_delete_btn.clicked.connect(self.delete_current_rule)
        self.new_rule_btn.clicked.connect(self.on_new_rule_mode)
        # 初期UI状態の更新
        self.update_ui_state()
        self.update_tab_styles()
    
    def create_history_menu(self):
        """履歴メニューを作成（モード別フィルタリング）"""
        menu = QMenu(self)
        # 現在のモードのルールのみを表示
        filtered_rules = self.rule_service.get_rules(self.current_mode)
        for rule in filtered_rules:
            rule_id = rule.get('id')
            title = rule.get('title', '')
            if rule_id is not None:
                action = menu.addAction(title)
                action.triggered.connect(lambda checked, rid=rule_id: self.apply_history_rule(rid))
        
        self.history_btn.setMenu(menu)
        self.history_btn.setPopupMode(QToolButton.InstantPopup)
    
    def on_mode_changed(self, new_mode: str):
        """モード変更時の処理"""
        logger.info(f"AIPanel: Mode changed from {self.current_mode} to {new_mode}")
        self.current_mode = new_mode
        
        # 履歴メニューを更新（新しいモードのルールのみ表示）
        self.create_history_menu()
        
        # 現在選択中のルールが新しいモードに対応していない場合はクリア
        if self.current_rule_id is not None:
            current_rule = next((r for r in self.rule_service.get_rules() if r.get('id') == self.current_rule_id), None)
            if current_rule and current_rule.get('mode', ProcessMode.NORMAL) != new_mode:
                logger.info(f"Current rule mode mismatch, clearing rule selection")
                self.current_rule_id = None
                self.update_ui_state()
        
        logger.info(f"AIPanel mode change completed for mode: {new_mode}")
    
    def show_auto_generate_message(self):
        """自動生成ボタン押下時の動作"""
        QToolTip.showText(self.auto_generate_btn.mapToGlobal(self.auto_generate_btn.rect().center()), 
                        "自動生成実行中...", self)
    
    def show_rule_detail_dialog(self):
        """ルール詳細編集ダイアログを表示する"""
        if self.current_rule_id is None:
            return
        rule_data = self.rule_map.get(self.current_rule_id)
        if not rule_data:
            logger.error(f"ルールデータが見つかりません id={self.current_rule_id}")
            return
        old_title = rule_data.get('title', '')
        old_prompt = rule_data.get('prompt', '')
        dlg = RuleEditDialog(self, rule_id=self.current_rule_id, title=old_title, prompt=old_prompt)
        if dlg.exec() == QDialog.Accepted:
            new_title, new_prompt = dlg.get_data()
            success = self.rule_service.update_rule(self.current_rule_id, {'title': new_title, 'prompt': new_prompt})
            if success:
                # メニューアイテム更新
                for act in self.history_btn.menu().actions():
                    if act.text() == old_title:
                        act.setText(new_title)
                        break
                # ローカルデータ更新
                self.rule_map[self.current_rule_id]['title'] = new_title
                self.rule_map[self.current_rule_id]['prompt'] = new_prompt
                self.update_ui_state()
                QToolTip.showText(self.rule_detail_btn.mapToGlobal(self.rule_detail_btn.rect().center()), f"ルール「{new_title}」を保存しました", self)
            else:
                QToolTip.showText(self.rule_detail_btn.mapToGlobal(self.rule_detail_btn.rect().center()), "ルール更新に失敗しました", self)
    
    def update_ui_state(self):
        """UI要素を現在のルール状態に応じて更新"""
        if self.current_rule_id is None:
            logger.debug("現在のルールなし、UIを更新します")
            self.rule_content.setText("ルール未作成")
            # ルール未生成時はプロンプトを非表示
            self.prompt_content.hide()
            # 詳細編集ボタンは非表示にする
            self.rule_detail_btn.hide()
            # 削除ボタンも非表示にする
            self.rule_delete_btn.hide()
            # 新規作成ボタンも非表示にする（ルール未作成時はタブ不要）
            self.new_rule_btn.hide()
            # サンプル生成ボタンはデフォルト文言に戻す
            self.auto_generate_btn.setText("テンプレートからルール生成")
            self.process_selected_btn.setEnabled(False)
            self.process_all_btn.setEnabled(False)
            # 処理ボタンを無効化し、灰色表示
            self.process_selected_btn.setStyleSheet("padding: 8px; background-color: #E0E0E0; color: #A0A0A0; border-radius: 3px;")
            self.process_all_btn.setStyleSheet("padding: 8px; background-color: #E0E0E0; color: #A0A0A0; border-radius: 3px;")
            logger.debug("処理ボタンを無効化しました")
        else:
            # 選択中ルールのタイトルを表示
            title = self.rule_map.get(self.current_rule_id, {}).get('title', str(self.current_rule_id))
            logger.debug(f"ルール id={self.current_rule_id} ('{title}') 適用、UIを更新します")
            self.rule_content.setText(title)
            # ルール生成時はプロンプトを設定して表示
            prompt = self.rule_map.get(self.current_rule_id, {}).get('prompt', '')
            self.prompt_content.setText(prompt)
            self.prompt_content.show()
            # 詳細編集ボタンを表示
            self.rule_detail_btn.show()
            # 削除ボタンを表示
            self.rule_delete_btn.show()
            # 新規作成ボタンを表示（ルール存在時はタブ切り替え可能）
            self.new_rule_btn.show()
            # サンプル生成ボタンの文言を変更
            self.auto_generate_btn.setText("再生成する")
            self.process_selected_btn.setEnabled(True)
            self.process_all_btn.setEnabled(True)
            # 処理ボタンを有効化し、新しい配色で表示
            selected_button_style = "padding: 8px; background-color: #4B918B; color: white; border-radius: 3px; font-weight: bold;"  # ティール色に変更
            all_button_style = "padding: 8px; background-color: #4B918B; color: white; border-radius: 3px; font-weight: bold;"  # ティール色
            self.process_selected_btn.setStyleSheet(selected_button_style)
            self.process_all_btn.setStyleSheet(all_button_style)
            logger.debug("処理ボタンを有効化しました")

    def apply_history_rule(self, rule_id: int):
        """履歴から選択したルールを適用"""
        title = self.rule_map.get(rule_id, {}).get('title', '')
        logger.debug(f"apply_history_rule called with rule_id={rule_id}, title='{title}'")
        self.current_rule_id = rule_id
        # 履歴選択モードに切り替え
        self.is_new_rule_mode = False
        self.update_ui_state()
        self.update_tab_styles()
        QToolTip.showText(self.history_btn.mapToGlobal(self.history_btn.rect().center()), 
                          f"ルール「{title}」を適用しました", self)
        rule_data = self.rule_map.get(rule_id)
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
        # IDベースのリストとマッピングを作成
        self.history_rules = [r.get('id') for r in self.rules_data]
        self.rule_map = {r.get('id'): r for r in self.rules_data}
        logger.debug(f"rules_data loaded: IDs {self.history_rules}")
        logger.debug(f"rule_map keys: {list(self.rule_map.keys())}")

    def on_auto_generate(self):
        """自動生成ボタンで新規ルールを生成し適用"""
        # 処理中メッセージ表示
        self.show_auto_generate_message()
        # 現在のルールIDを退避
        old_rule_id = self.current_rule_id
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
        
        # UIロックとスピナー表示
        self.auto_generate_btn.setEnabled(False)
        self.rule_detail_btn.setEnabled(False)
        self.history_btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        logger.info(f"ルール生成開始: 入力サンプル数={len(samples)}件")
        
        # RuleCreationWorkerを使用して非同期実行
        self.rule_creation_worker = RuleCreationWorker(
            self.rule_service,
            samples,
            self.current_mode,
            old_rule_id  # 新規作成時はNone、再生成時はルールID
        )
        self.rule_creation_worker.finished.connect(self.on_rule_creation_finished)
        self.rule_creation_worker.error_occurred.connect(self.on_rule_creation_error)
        self.rule_creation_worker.start()

    def on_rule_creation_finished(self, metadata):
        """ルール作成・再生成完了時の処理"""
        try:
            new_id = metadata.get('id')
            new_title = metadata.get('rule_name', metadata.get('title', ''))
            
            # UIにルールを追加
            if new_id not in self.history_rules:
                self.rules_data.append(metadata)
                self.history_rules.append(new_id)
                self.rule_map[new_id] = metadata
                # 履歴メニューを再構築（モード別フィルタリング適用）
                self.create_history_menu()
            
            # 新ルールを適用
            self.apply_history_rule(new_id)
            # 新規作成完了後は新規作成モードに
            self.is_new_rule_mode = True
            self.update_tab_styles()
            logger.info(f"ルール生成完了: id={new_id}, title='{new_title}', mode={self.current_mode}")
            
        except Exception as e:
            logger.error(f"ルール生成後処理エラー: {e}")
        finally:
            # UIロック解除とカーソル復帰
            self.auto_generate_btn.setEnabled(True)
            self.rule_detail_btn.setEnabled(True)
            self.history_btn.setEnabled(True)
            QApplication.restoreOverrideCursor()

    def on_rule_creation_error(self, error_message):
        """ルール作成・再生成エラー時の処理"""
        logger.error(f"ルール生成エラー: {error_message}")
        QToolTip.showText(self.auto_generate_btn.mapToGlobal(self.auto_generate_btn.rect().center()),
                          f"ルール生成中にエラーが発生しました: {error_message}", self)
        # UIロック解除とカーソル復帰
        self.auto_generate_btn.setEnabled(True)
        self.rule_detail_btn.setEnabled(True)
        self.history_btn.setEnabled(True)
        QApplication.restoreOverrideCursor()

    def delete_current_rule(self):
        """選択中のルールを削除する"""
        if self.current_rule_id is None:
            logger.debug("delete_current_rule: current_rule_id が None なので何もしない")
            return

        title = self.rule_map.get(self.current_rule_id, {}).get('title', '')
        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "確認",
            f"ルール「{title}」を本当に削除しますか？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            logger.info(f"ルール削除キャンセル id={self.current_rule_id}")
            return

        logger.info(f"ルール削除開始 id={self.current_rule_id}")
        success = self.rule_service.delete_rule(self.current_rule_id)
        if success:
            # 内部データも削除
            self.history_rules.remove(self.current_rule_id)
            del self.rule_map[self.current_rule_id]
            # 履歴メニューを再構築（削除されたルールは自動的に除外される）
            self.create_history_menu()
            # 選択解除・UI更新
            self.current_rule_id = None
            self.update_ui_state()
            QToolTip.showText(
                self.rule_delete_btn.mapToGlobal(self.rule_delete_btn.rect().center()),
                "ルールを削除しました", self
            )
            logger.info(f"ルール削除完了")
        else:
            logger.warning(f"ルール削除失敗 id={self.current_rule_id}")
            QToolTip.showText(
                self.rule_delete_btn.mapToGlobal(self.rule_delete_btn.rect().center()),
                "ルールの削除に失敗しました", self
            )

    def on_new_rule_mode(self):
        """新規作成モードに切り替える"""
        self.is_new_rule_mode = True
        self.current_rule_id = None
        self.update_ui_state()
        self.update_tab_styles()
        
        # サンプルテーブルもクリアする
        if hasattr(self, 'excel_panel') and self.excel_panel:
            try:
                self.excel_panel.clear_sample_data()
                logger.info("リセット時にサンプルテーブルをクリアしました")
            except Exception as e:
                logger.error(f"サンプルテーブルクリアエラー: {e}")
        
        QToolTip.showText(self.new_rule_btn.mapToGlobal(self.new_rule_btn.rect().center()), 
                          "リセットしました", self)

    def update_tab_styles(self):
        """タブのスタイルを更新する"""
        if self.is_new_rule_mode:
            # 新規作成モード：新規作成ボタンを選択状態、履歴ボタンを非選択状態
            self.new_rule_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4B918B; 
                    color: white; 
                    font-size: 12px; 
                    font-weight: bold; 
                    padding: 5px 15px; 
                    border-radius: 3px;
                    border: 2px solid #4B918B;
                }
                QPushButton:hover {
                    background-color: #3A7169;
                }
            """)
            self.history_btn.setStyleSheet("""
                QToolButton {
                    background-color: #E8EEF4; 
                    color: #3A506B; 
                    font-size: 12px; 
                    padding: 5px 15px; 
                    border-radius: 3px;
                    border: 2px solid #D1D9E6;
                }
                QToolButton:hover {
                    background-color: #D1D9E6;
                }
            """)
        else:
            # 履歴選択モード：履歴ボタンを選択状態、新規作成ボタンを非選択状態
            self.new_rule_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E8EEF4; 
                    color: #3A506B; 
                    font-size: 12px; 
                    padding: 5px 15px; 
                    border-radius: 3px;
                    border: 2px solid #D1D9E6;
                }
                QPushButton:hover {
                    background-color: #D1D9E6;
                }
            """)
            self.history_btn.setStyleSheet("""
                QToolButton {
                    background-color: #4B918B; 
                    color: white; 
                    font-size: 12px; 
                    padding: 5px 15px; 
                    border-radius: 3px;
                    border: 2px solid #4B918B;
                }
                QToolButton:hover {
                    background-color: #3A7169;
                }
            """)