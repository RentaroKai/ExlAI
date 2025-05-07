import sys
import logging
import os
# ログファイルパス設定
LOG_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'app.log'))
# ファイルログハンドラ設定
file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logging.getLogger().addHandler(file_handler)
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter, QMessageBox
from PySide6.QtCore import Qt

from app.ui.excel_panel import ExcelPanel
from app.ui.ai_panel import AIPanel
from app.ui.config_dialog import ConfigDialog

class IntegratedExcelUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIエクセル - 統合UI")
        self.setGeometry(100, 100, 1300, 700)
        # メニューバーの作成
        menubar = self.menuBar()
        file_menu = menubar.addMenu("ファイル")
        # CSV入出力アクション
        from PySide6.QtWidgets import QFileDialog
        load_csv_act = file_menu.addAction("CSV読み込み")
        load_csv_act.triggered.connect(self.load_csv)
        save_csv_act = file_menu.addAction("CSV保存")
        save_csv_act.triggered.connect(self.save_csv)
        settings_menu = menubar.addMenu("設定")
        config_act = settings_menu.addAction("環境設定")
        config_act.triggered.connect(self.open_config_dialog)
        
        # メインウィジェット
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #cceedd; color: #333333;")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # スプリッター (左右の領域を区切るためのもの)
        h_splitter = QSplitter(Qt.Horizontal)
        
        # 左側：エクセルパネル
        self.excel_panel = ExcelPanel()
        
        # 右側：AIパネル
        # AIPanelを生成し、ExcelPanelへの参照を持たせる
        self.ai_panel = AIPanel()
        self.ai_panel.excel_panel = self.excel_panel
        
        # 水平スプリッターに左右のパネルを追加
        h_splitter.addWidget(self.excel_panel)
        h_splitter.addWidget(self.ai_panel)
        
        # 水平スプリッターの初期サイズ比率を設定（左:右 = 7:3）
        h_splitter.setSizes([700, 300])
        
        # メインレイアウトにスプリッターを追加
        main_layout.addWidget(h_splitter)
        
        # パネル間の連携を設定
        self.connect_panels()
    
    def connect_panels(self):
        """左側パネルと右側パネル間の連携を設定"""
        # 処理ボタンのイベント接続
        self.ai_panel.process_selected_btn.clicked.connect(self.process_selected)
        self.ai_panel.process_all_btn.clicked.connect(self.process_all)
    
    def process_selected(self):
        """選択行のみ処理する"""
        # 現在のルールチェック
        rule_id = self.ai_panel.current_rule_id
        if rule_id is None:
            from PySide6.QtWidgets import QToolTip
            QToolTip.showText(self.ai_panel.process_selected_btn.mapToGlobal(self.ai_panel.process_selected_btn.rect().center()), "ルールが選択されていません", self)
            return
        # 処理対象テーブルを判定
        if self.excel_panel.sample_table.hasFocus():
            active_table = self.excel_panel.sample_table
        else:
            active_table = self.excel_panel.data_table
        # 選択行取得
        selected_items = active_table.selectedItems()
        rows = sorted({item.row() for item in selected_items if item.row() > 0})
        if not rows:
            return
        # 入力文字列リスト作成
        inputs = []
        for row in rows:
            item = active_table.item(row, 1)
            inputs.append(item.text() if item and item.text() else "")
        # 処理前に進捗を「処理中」に設定
        from PySide6.QtWidgets import QTableWidgetItem
        for row in rows:
            in_progress = QTableWidgetItem("処理中")
            in_progress.setTextAlignment(Qt.AlignCenter)
            active_table.setItem(row, 0, in_progress)
        # UI更新を強制
        QApplication.processEvents()
        # UIロックとスピナー表示 & 処理開始ログ
        self.ai_panel.process_selected_btn.setEnabled(False)
        self.ai_panel.process_all_btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        logger.info(f"apply_rule 開始: rule_id={rule_id} 対象行数={len(inputs)}件")
        try:
            results = self.ai_panel.rule_service.apply_rule(rule_id, inputs)
            from PySide6.QtWidgets import QTableWidgetItem
            for row, result in zip(rows, results):
                status = result.get('status')
                text = "完了" if status == 'success' else "エラー"
                check_item = QTableWidgetItem(text)
                check_item.setTextAlignment(Qt.AlignCenter)
                if status != 'success':
                    check_item.setToolTip(result.get('error_msg', ''))
                active_table.setItem(row, 0, check_item)
                # 出力フィールド更新
                output = result.get('output', {})
                for header, val in output.items():
                    for c in range(active_table.columnCount()):
                        hdr = active_table.item(0, c)
                        if hdr and hdr.text() == header:
                            active_table.setItem(row, c, QTableWidgetItem(val))
                            break
            # 処理完了ログ
            success_count = sum(1 for r in results if r.get('status') == 'success')
            error_count = len(results) - success_count
            logger.info(f"apply_rule 完了: success={success_count}件 error={error_count}件")
        except Exception as e:
            logger.error(f"apply_rule 中断: {e}")
            # 例外ダイアログ表示
            msg = QMessageBox(self)
            msg.setWindowTitle("エラーが発生しました")
            msg.setText("処理中に予期せぬエラーが発生しました")
            open_btn = msg.addButton("ログファイルを開く", QMessageBox.AcceptRole)
            msg.exec()
            if msg.clickedButton() == open_btn:
                os.startfile(LOG_FILE_PATH)
        finally:
            # UIロック解除
            self.ai_panel.process_selected_btn.setEnabled(True)
            self.ai_panel.process_all_btn.setEnabled(True)
            QApplication.restoreOverrideCursor()
    
    def process_all(self):
        """すべての行を処理する"""
        rule_id = self.ai_panel.current_rule_id
        if rule_id is None:
            from PySide6.QtWidgets import QToolTip
            QToolTip.showText(self.ai_panel.process_all_btn.mapToGlobal(self.ai_panel.process_all_btn.rect().center()), "ルールが選択されていません", self)
            return
        # 実データパネルの未処理行のみを対象に処理
        tbl = self.excel_panel.data_table
        # 対象行の抽出 (AI進捗列が空, '未処理', 'エラー')
        rows = []
        for row in range(1, tbl.rowCount()):
            # AI進捗セルの状態を取得
            item = tbl.item(row, 0)
            status_text = item.text().strip() if item and item.text() else ""
            # 元の値セルのテキストを取得
            cell = tbl.item(row, 1)
            input_text = cell.text().strip() if cell and cell.text() else ""
            # 元の値セルが空の場合はスキップ
            if input_text == "":
                logger.debug(f"process_all: スキップ - row {row} の元の値セルが空です")
                continue
            # ステータスが未処理またはエラーの場合のみ処理対象に追加
            if status_text in ["", "未処理", "エラー"]:
                rows.append(row)
        if not rows:
            return
        # 処理前に進捗を「処理中」に設定
        from PySide6.QtWidgets import QTableWidgetItem
        for row in rows:
            in_progress = QTableWidgetItem("処理中")
            in_progress.setTextAlignment(Qt.AlignCenter)
            tbl.setItem(row, 0, in_progress)
        QApplication.processEvents()
        # 入力文字列リスト作成
        inputs = []
        for row in rows:
            cell = tbl.item(row, 1)
            inputs.append(cell.text() if cell and cell.text() else "")
        # UIロックとスピナー表示 & 処理開始ログ
        self.ai_panel.process_selected_btn.setEnabled(False)
        self.ai_panel.process_all_btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        logger.info(f"apply_rule 開始: rule_id={rule_id} 対象行数={len(inputs)}件")
        try:
            results = self.ai_panel.rule_service.apply_rule(rule_id, inputs)
            from PySide6.QtWidgets import QTableWidgetItem
            for row, result in zip(rows, results):
                status = result.get('status')
                text = "完了" if status == 'success' else "エラー"
                check_item = QTableWidgetItem(text)
                check_item.setTextAlignment(Qt.AlignCenter)
                if status != 'success':
                    check_item.setToolTip(result.get('error_msg', ''))
                tbl.setItem(row, 0, check_item)
                # 出力フィールド更新
                output = result.get('output', {})
                for header, val in output.items():
                    for c in range(tbl.columnCount()):
                        hdr = tbl.item(0, c)
                        if hdr and hdr.text() == header:
                            tbl.setItem(row, c, QTableWidgetItem(val))
                            break
            # 処理完了ログ
            success_count = sum(1 for r in results if r.get('status') == 'success')
            error_count = len(results) - success_count
            logger.info(f"apply_rule 完了: success={success_count}件 error={error_count}件")
        except Exception as e:
            logger.error(f"apply_rule 中断: {e}")
            # 例外ダイアログ表示
            msg = QMessageBox(self)
            msg.setWindowTitle("エラーが発生しました")
            msg.setText("処理中に予期せぬエラーが発生しました")
            open_btn = msg.addButton("ログファイルを開く", QMessageBox.AcceptRole)
            msg.exec()
            if msg.clickedButton() == open_btn:
                os.startfile(LOG_FILE_PATH)
        finally:
            # UIロック解除
            self.ai_panel.process_selected_btn.setEnabled(True)
            self.ai_panel.process_all_btn.setEnabled(True)
            QApplication.restoreOverrideCursor()

    def load_csv(self):
        from PySide6.QtWidgets import QFileDialog
        import logging
        file_path, _ = QFileDialog.getOpenFileName(self, "CSV読み込み", "", "CSV files (*.csv)")
        if file_path:
            try:
                self.excel_panel.load_csv(file_path)
            except Exception as e:
                logging.error(f"CSV読み込みエラー: {e}")

    def save_csv(self):
        from PySide6.QtWidgets import QFileDialog
        import logging
        file_path, _ = QFileDialog.getSaveFileName(self, "CSV保存", "", "CSV files (*.csv)")
        if file_path:
            try:
                self.excel_panel.save_csv(file_path)
            except Exception as e:
                logging.error(f"CSV保存エラー: {e}")

    def open_config_dialog(self):
        """設定ダイアログを開く"""
        dlg = ConfigDialog(self)
        dlg.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IntegratedExcelUI()
    window.show()
    sys.exit(app.exec()) 