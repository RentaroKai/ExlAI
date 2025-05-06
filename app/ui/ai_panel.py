import sys
import logging
from app.services.rule_service import RuleService
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
        self.rule_service = RuleService()
        self.load_rules_from_json()
        self.setup_ui()
        
    def setup_ui(self):
        """AIパネルのUI設定"""
        # レイアウト設定
        self.setStyleSheet("background-color: #F5F7FA; color: #333333;")  # 背景色をExcelパネルと統一
        ai_layout = QVBoxLayout(self)
        ai_layout.setContentsMargins(15, 15, 15, 15)
        ai_layout.setSpacing(15)  # 均等な余白
        
        # AIパネルタイトルとボタンを含む上部レイアウト
        top_layout = QHBoxLayout()
        
        # AIパネルタイトル（左上に配置）
        ai_title = QLabel("AI_panel")
        ai_title.setFont(QFont("Arial", 12, QFont.Bold))
        ai_title.setStyleSheet("color: #3A506B;")  # テンプレートラベルと同じ色
        top_layout.addWidget(ai_title)
        
        # 右側にスペースを追加
        top_layout.addStretch()
        
        # 履歴ボタン（右上に配置）
        self.history_btn = QToolButton()
        self.history_btn.setText("📋 履歴")
        self.history_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.history_btn.setStyleSheet("color: #3A506B; background-color: transparent;")
        self.history_btn.setToolTip("過去の履歴からルールを適用します")
        top_layout.addWidget(self.history_btn)
        # ヒストリールールメニュー設定（IDベース）
        menu = QMenu(self)
        for rid in self.history_rules:
            title = self.rule_map.get(rid, {}).get('title', '')
            action = menu.addAction(title)
            action.triggered.connect(lambda checked, rule_id=rid: self.apply_history_rule(rule_id))
        self.history_btn.setMenu(menu)
        self.history_btn.setPopupMode(QToolButton.InstantPopup)
        # 上部レイアウトをパネルに追加
        ai_layout.addLayout(top_layout)
        
        # 処理ルール表示フレーム
        rule_frame = QFrame()
        rule_frame.setFrameShape(QFrame.StyledPanel)
        rule_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #D1D9E6;")  # 枠線色を統一
        rule_layout = QVBoxLayout(rule_frame)
        
        # 処理ルールのタイトル
        rule_title = QLabel("処理ルール")
        rule_title.setFont(QFont("Arial", 12, QFont.Bold))
        rule_title.setStyleSheet("color: #3A506B;")  # タイトル色を統一
        rule_layout.addWidget(rule_title)
        
        # ルール内容 - 左寄せにして大きいフォントに変更
        self.rule_content = QLabel("ルール未作成")
        self.rule_content.setAlignment(Qt.AlignLeft)  # 左寄せに変更
        self.rule_content.setFont(QFont("Arial", 14))  # フォントサイズを14に変更
        self.rule_content.setStyleSheet("color: #333333; padding: 10px;")
        rule_layout.addWidget(self.rule_content)
        
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
        process_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #D1D9E6;")  # 枠線色を統一
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
        selected_button_style = "padding: 8px; background-color: #5D4A66; color: white; border-radius: 3px; font-weight: bold;"  # データエリアラベルと同じ色
        all_button_style = "padding: 8px; background-color: #4B918B; color: white; border-radius: 3px; font-weight: bold;"  # ティール色
        self.process_selected_btn.setStyleSheet(selected_button_style)
        self.process_all_btn.setStyleSheet(all_button_style)
        
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
        self.rule_detail_btn.clicked.connect(self.show_rule_detail_dialog)
        self.rule_delete_btn.clicked.connect(self.delete_current_rule)
        # 初期UI状態の更新
        self.update_ui_state()
    
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
            # 詳細編集ボタンは非表示にする
            self.rule_detail_btn.hide()
            # 削除ボタンも非表示にする
            self.rule_delete_btn.hide()
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
            # 詳細編集ボタンを表示
            self.rule_detail_btn.show()
            # 削除ボタンを表示
            self.rule_delete_btn.show()
            # サンプル生成ボタンの文言を変更
            self.auto_generate_btn.setText("再生成する")
            self.process_selected_btn.setEnabled(True)
            self.process_all_btn.setEnabled(True)
            # 処理ボタンを有効化し、新しい配色で表示
            selected_button_style = "padding: 8px; background-color: #5D4A66; color: white; border-radius: 3px; font-weight: bold;"  # データエリアラベルと同じ色
            all_button_style = "padding: 8px; background-color: #4B918B; color: white; border-radius: 3px; font-weight: bold;"  # ティール色
            self.process_selected_btn.setStyleSheet(selected_button_style)
            self.process_all_btn.setStyleSheet(all_button_style)
            logger.debug("処理ボタンを有効化しました")

    def apply_history_rule(self, rule_id: int):
        """履歴から選択したルールを適用"""
        title = self.rule_map.get(rule_id, {}).get('title', '')
        logger.debug(f"apply_history_rule called with rule_id={rule_id}, title='{title}'")
        self.current_rule_id = rule_id
        self.update_ui_state()
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
        # ルール生成または再生成API呼び出し
        # UIロックとスピナー表示
        self.auto_generate_btn.setEnabled(False)
        self.rule_detail_btn.setEnabled(False)
        self.history_btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        logger.info(f"ルール生成開始: 入力サンプル数={len(samples)}件")
        try:
            # ルール作成 or 再生成
            if old_rule_id is None:
                metadata = self.rule_service.create_rule(samples)
            else:
                metadata = self.rule_service.regenerate_rule(old_rule_id, samples)
            new_id = metadata.get('id')
            new_title = metadata.get('rule_name')
            # UIにルールを追加
            if new_id not in self.history_rules:
                self.rules_data.append(metadata)
                self.history_rules.append(new_id)
                self.rule_map[new_id] = metadata
                action = self.history_btn.menu().addAction(new_title)
                action.triggered.connect(lambda _, rid=new_id: self.apply_history_rule(rid))
            # 旧ルールをメニューから削除（再生成時）
            if old_rule_id is not None and old_rule_id != new_id:
                old_title = self.rule_map.get(old_rule_id, {}).get('title', '')
                for act in self.history_btn.menu().actions():
                    if act.text() == old_title:
                        self.history_btn.menu().removeAction(act)
                        break
            # 新ルールを適用
            self.apply_history_rule(new_id)
            logger.info(f"ルール生成完了: id={new_id}, title='{new_title}'")
        except NotImplementedError:
            logger.error("create_rule未実装")
            QToolTip.showText(self.auto_generate_btn.mapToGlobal(self.auto_generate_btn.rect().center()),
                              "ルール生成機能が未実装です", self)
        except Exception as e:
            logger.error(f"ルール生成エラー: {e}")
            QToolTip.showText(self.auto_generate_btn.mapToGlobal(self.auto_generate_btn.rect().center()),
                              f"ルール生成中にエラーが発生しました: {e}", self)
        finally:
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
            # メニューからアクションを削除
            for act in self.history_btn.menu().actions():
                if act.text() == title:
                    self.history_btn.menu().removeAction(act)
                    logger.debug(f"メニューアイテム削除: {title}")
                    break
            # 内部データも削除
            self.history_rules.remove(self.current_rule_id)
            del self.rule_map[self.current_rule_id]
            # 選択解除・UI更新
            self.current_rule_id = None
            self.update_ui_state()
            QToolTip.showText(
                self.rule_delete_btn.mapToGlobal(self.rule_delete_btn.rect().center()),
                "ルールを削除しました", self
            )
            logger.info(f"ルール削除完了 id={self.current_rule_id}")
        else:
            logger.warning(f"ルール削除失敗 id={self.current_rule_id}")
            QToolTip.showText(
                self.rule_delete_btn.mapToGlobal(self.rule_delete_btn.rect().center()),
                "ルールの削除に失敗しました", self
            )