from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPlainTextEdit, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import Qt

import logging
logger = logging.getLogger(__name__)

class RuleEditDialog(QDialog):
    """ルールのタイトルとプロンプトを編集するダイアログ"""
    def __init__(self, parent=None, rule_id: int = None, title: str = "", prompt: str = ""):
        super().__init__(parent)
        self.rule_id = rule_id
        self.setWindowTitle("ルール詳細編集")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # ルールID表示
        id_label = QLabel(f"ルールID: {rule_id}")
        layout.addWidget(id_label)

        # タイトル編集
        layout.addWidget(QLabel("タイトル"))
        self.title_edit = QLineEdit(title)
        layout.addWidget(self.title_edit)

        # プロンプト編集
        layout.addWidget(QLabel("プロンプト"))
        self.prompt_edit = QPlainTextEdit(prompt)
        self.prompt_edit.setFixedHeight(200)
        layout.addWidget(self.prompt_edit)

        # 保存・キャンセルボタン
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.cancel_btn = QPushButton("キャンセル")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # イベント接続
        self.save_btn.clicked.connect(self.on_save)
        self.cancel_btn.clicked.connect(self.reject)

    def on_save(self):
        new_title = self.title_edit.text().strip()
        if not new_title:
            QMessageBox.warning(self, "入力エラー", "タイトルを入力してください")
            return
        logger.info(f"Saving edits for rule id={self.rule_id}: new title='{new_title}'")
        self.accept()

    def get_data(self):
        """編集後のタイトルとプロンプトを取得"""
        return self.title_edit.text().strip(), self.prompt_edit.toPlainText().strip() 