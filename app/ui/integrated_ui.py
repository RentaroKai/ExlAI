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
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter, 
                              QMessageBox, QVBoxLayout, QRadioButton, QButtonGroup, QLabel, QFrame,
                              QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.ui.excel_panel import ExcelPanel
from app.ui.ai_panel import AIPanel
from app.ui.config_dialog import ConfigDialog
from app.ui.help_dialog import HelpDialog
from app.workers import AIWorker

BACKUP_CSV_NAME = 'last_processed.csv'

class ProcessMode:
    """処理モード定義"""
    NORMAL = "normal"      # テキスト処理
    IMAGE = "image"        # 画像処理  
    VIDEO = "video"        # 動画処理

class IntegratedExcelUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIエクセル - 統合UI")
        self.setGeometry(100, 100, 1300, 700)
        
        # 現在のモード
        self.current_mode = ProcessMode.NORMAL
        
        # メニューバーの作成
        menubar = self.menuBar()
        file_menu = menubar.addMenu("ファイル")
        # CSV入出力アクション
        from PySide6.QtWidgets import QFileDialog
        load_csv_act = file_menu.addAction("CSV読み込み")
        load_csv_act.triggered.connect(self.load_csv)
        save_csv_act = file_menu.addAction("CSV保存")
        save_csv_act.triggered.connect(self.save_csv)
        # バックアップCSV開くアクション追加
        file_menu.addSeparator()
        open_last_act = file_menu.addAction("最後に処理したファイルを開く（バックアップ）")
        open_last_act.triggered.connect(self.open_backup)
        settings_menu = menubar.addMenu("設定")
        config_act = settings_menu.addAction("環境設定")
        config_act.triggered.connect(self.open_config_dialog)
        # ヘルプメニューの変更
        help_menu = menubar.addMenu("ヘルプ")
        help_act = help_menu.addAction("使い方ガイド")
        help_act.triggered.connect(self.open_help_dialog)
        
        # メインウィジェット
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #dadfdd; color: #333333;")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # モード選択UIの作成
        self.create_mode_selection_ui(main_layout)
        
        # コンテンツエリアのレイアウト
        content_layout = QHBoxLayout()
        
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
        
        # コンテンツレイアウトにスプリッターを追加
        content_layout.addWidget(h_splitter)
        
        # メインレイアウトにコンテンツレイアウトを追加（ストレッチファクター1で拡張可能）
        main_layout.addLayout(content_layout, 1)
        
        # パネル間の連携を設定
        self.connect_panels()
        
        # ワーカースレッド用変数の初期化
        self.ai_worker = None
    
    def create_mode_selection_ui(self, parent_layout):
        """モード選択UIを作成"""
        # モード選択フレーム
        mode_frame = QFrame()
        mode_frame.setFrameShape(QFrame.StyledPanel)
        mode_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CCCCCC; border-radius: 5px;")
        
        # フレームの高さを固定し、縮小しないよう設定
        mode_frame.setFixedHeight(50)  # 高さを50pxに固定
        mode_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 垂直方向のサイズポリシーを固定に設定
        
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(15, 10, 15, 10)
        mode_layout.setSpacing(20)
        
        # モード選択ラベル
        mode_label = QLabel("処理モード:")
        mode_label.setFont(QFont("Arial", 12, QFont.Bold))
        mode_label.setStyleSheet("color: #333333; border: none;")
        mode_layout.addWidget(mode_label)
        
        # ラジオボタングループの作成
        self.mode_button_group = QButtonGroup()
        
        # テキスト処理ラジオボタン
        self.normal_radio = QRadioButton("テキスト処理")
        self.normal_radio.setChecked(True)  # デフォルトで選択
        self.normal_radio.setFont(QFont("Arial", 10))
        self.normal_radio.setStyleSheet("color: #333333; border: none;")
        
        # 画像処理ラジオボタン
        self.image_radio = QRadioButton("画像処理")
        self.image_radio.setFont(QFont("Arial", 10))
        self.image_radio.setStyleSheet("color: #333333; border: none;")
        
        # 動画処理ラジオボタン
        self.video_radio = QRadioButton("動画処理")
        self.video_radio.setFont(QFont("Arial", 10))
        self.video_radio.setStyleSheet("color: #333333; border: none;")
        
        # ラジオボタンをグループに追加
        self.mode_button_group.addButton(self.normal_radio, 0)
        self.mode_button_group.addButton(self.image_radio, 1)
        self.mode_button_group.addButton(self.video_radio, 2)
        
        # モード切替時のイベント接続
        self.mode_button_group.buttonClicked.connect(self.on_mode_changed)
        
        # レイアウトに追加
        mode_layout.addWidget(self.normal_radio)
        mode_layout.addWidget(self.image_radio)
        mode_layout.addWidget(self.video_radio)
        mode_layout.addStretch()  # 右側にスペースを追加
        
        # 親レイアウトに追加（ストレッチファクター0で固定サイズ）
        parent_layout.addWidget(mode_frame, 0)
    
    def on_mode_changed(self, button):
        """モード変更時の処理"""
        button_id = self.mode_button_group.id(button)
        if button_id == 0:
            self.current_mode = ProcessMode.NORMAL
            logger.info("モード変更: テキスト処理")
        elif button_id == 1:
            self.current_mode = ProcessMode.IMAGE
            logger.info("モード変更: 画像処理")
        elif button_id == 2:
            self.current_mode = ProcessMode.VIDEO
            logger.info("モード変更: 動画処理")
        
        # モード変更をAIパネルに通知（今後の実装で使用）
        if hasattr(self.ai_panel, 'on_mode_changed'):
            self.ai_panel.on_mode_changed(self.current_mode)
        
        # モード変更をExcelパネルに通知（今後の実装で使用）
        if hasattr(self.excel_panel, 'on_mode_changed'):
            self.excel_panel.on_mode_changed(self.current_mode)
    
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
            
        # 選択されたルールの情報を取得
        selected_rule = next((r for r in self.ai_panel.rule_service.get_rules() if r.get('id') == rule_id), None)
        rule_mode = selected_rule.get('mode', 'normal') if selected_rule else 'normal'
        
        # 処理対象テーブルを判定
        if self.excel_panel.sample_table.hasFocus():
            active_table = self.excel_panel.sample_table
        else:
            active_table = self.excel_panel.data_table
            
        # 選択行取得
        selected_items = active_table.selectedItems()
        rows = sorted({item.row() for item in selected_items if item.row() > 0})
        if not rows:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "選択なし", "処理する行を選択してください。")
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
        
        # モード別の処理メッセージ
        if rule_mode == 'image':
            processing_msg = f"画像解析処理を開始しています... ({len(inputs)}件)"
        elif rule_mode == 'video':
            processing_msg = f"動画解析処理を開始しています... ({len(inputs)}件)"
        else:
            processing_msg = f"テキスト処理を開始しています... ({len(inputs)}件)"
            
        logger.info(processing_msg)
        
        # UIロック表示
        self.ai_panel.process_selected_btn.setEnabled(False)
        self.ai_panel.process_all_btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        # ワーカースレッドでAI処理を実行
        logger.info(f"process_selected 開始: rule_id={rule_id} mode={rule_mode} 対象行数={len(inputs)}件")
        self.ai_worker = AIWorker(self.ai_panel.rule_service, rule_id, inputs)
        
        # 処理完了とエラーハンドリングのシグナル接続
        self.ai_worker.finished.connect(lambda results: self._on_process_selected_finished(results, rows, active_table))
        self.ai_worker.error_occurred.connect(self._on_process_selected_error)
        
        # ワーカースレッド開始
        self.ai_worker.start()
    
    def _on_process_selected_finished(self, results, rows, active_table):
        """process_selected処理完了時のコールバック"""
        try:
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
            
            # バックアップCSVを保存
            try:
                base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(sys.argv[0]))
                backup_path = os.path.join(base_dir, BACKUP_CSV_NAME)
                self.excel_panel.save_csv(backup_path)
                logger.info(f"バックアップ保存完了: {backup_path}")
            except Exception as e:
                logger.error(f"バックアップ保存エラー: {e}")
                
        finally:
            # UIロック解除
            self.ai_panel.process_selected_btn.setEnabled(True)
            self.ai_panel.process_all_btn.setEnabled(True)
            QApplication.restoreOverrideCursor()
            
    def _on_process_selected_error(self, error_msg):
        """process_selected処理エラー時のコールバック"""
        logger.error(f"apply_rule 中断: {error_msg}")
        
        # エラーダイアログ表示
        msg = QMessageBox(self)
        msg.setWindowTitle("エラーが発生しました")
        msg.setText("処理中に予期せぬエラーが発生しました")
        open_btn = msg.addButton("ログファイルを開く", QMessageBox.AcceptRole)
        msg.exec()
        if msg.clickedButton() == open_btn:
            os.startfile(LOG_FILE_PATH)
            
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
        # UIロック表示
        self.ai_panel.process_selected_btn.setEnabled(False)
        self.ai_panel.process_all_btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        # ワーカースレッドでAI処理を実行
        logger.info(f"process_all 開始: rule_id={rule_id} 対象行数={len(inputs)}件")
        self.ai_worker = AIWorker(self.ai_panel.rule_service, rule_id, inputs)
        
        # 処理完了とエラーハンドリングのシグナル接続
        self.ai_worker.finished.connect(lambda results: self._on_process_all_finished(results, rows, tbl))
        self.ai_worker.error_occurred.connect(self._on_process_all_error)
        
        # ワーカースレッド開始
        self.ai_worker.start()

    def _on_process_all_finished(self, results, rows, tbl):
        """process_all処理完了時のコールバック"""
        try:
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
            
            # バックアップCSVを保存
            try:
                base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(sys.argv[0]))
                backup_path = os.path.join(base_dir, BACKUP_CSV_NAME)
                self.excel_panel.save_csv(backup_path)
                logger.info(f"バックアップ保存完了: {backup_path}")
            except Exception as e:
                logger.error(f"バックアップ保存エラー: {e}")
                
        finally:
            # UIロック解除
            self.ai_panel.process_selected_btn.setEnabled(True)
            self.ai_panel.process_all_btn.setEnabled(True)
            QApplication.restoreOverrideCursor()
            
    def _on_process_all_error(self, error_msg):
        """process_all処理エラー時のコールバック"""
        logger.error(f"apply_rule 中断: {error_msg}")
        
        # エラーダイアログ表示
        msg = QMessageBox(self)
        msg.setWindowTitle("エラーが発生しました")
        msg.setText("処理中に予期せぬエラーが発生しました")
        open_btn = msg.addButton("ログファイルを開く", QMessageBox.AcceptRole)
        msg.exec()
        if msg.clickedButton() == open_btn:
            os.startfile(LOG_FILE_PATH)
            
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

    def open_help_dialog(self):
        """ヘルプダイアログを表示する"""
        dialog = HelpDialog(self)
        dialog.exec()

    # バックアップCSVを開く
    def open_backup(self):
        """最後に処理したCSVバックアップファイルを開く"""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        backup_path = os.path.join(base_dir, BACKUP_CSV_NAME)
        if os.path.exists(backup_path):
            try:
                logger.info(f"バックアップファイルを開く: {backup_path}")
                os.startfile(backup_path)
            except Exception as e:
                logger.error(f"バックアップファイルのオープンエラー: {e}")
                msg = QMessageBox(self)
                msg.setWindowTitle("エラー")
                msg.setText("バックアップファイルを開くことができませんでした")
                msg.exec()
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("ファイルが見つかりません")
            msg.setText("バックアップファイルが存在しません")
            msg.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IntegratedExcelUI()
    window.show()
    sys.exit(app.exec()) 