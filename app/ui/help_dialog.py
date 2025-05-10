import os
import sys
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTabWidget, QWidget, QPushButton, QScrollArea, 
                             QTextEdit, QGroupBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont, QIcon

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ExlAI - ヘルプ")
        self.setMinimumSize(800, 600)
        
        # アイコンの設定
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # メインレイアウト
        main_layout = QVBoxLayout(self)
        
        # ヘッダー部分
        header_layout = QHBoxLayout()
        
        # ロゴ画像
        logo_label = QLabel()
        logo_path = os.path.join(base_dir, "ExlAI.jpg")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # タイトルと説明
        title_layout = QVBoxLayout()
        title_label = QLabel("ExlAI")
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        subtitle_label = QLabel("エクセル風AIアシスタント - 基本ガイド")
        subtitle_label.setFont(QFont("Arial", 14))
        desc_label = QLabel("「こんなふうに処理できたらいいな」というイメージを入力するだけで、\nAIが自動的にデータを一括処理してくれます！")
        desc_label.setWordWrap(True)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.addWidget(desc_label)
        title_layout.addStretch()
        
        header_layout.addWidget(logo_label)
        header_layout.addLayout(title_layout)
        
        # タブウィジェット
        tab_widget = QTabWidget()
        
        # 基本的な使い方タブ
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # このアプリで何ができるの？
        features_group = QGroupBox("このアプリで何ができるの？")
        features_layout = QVBoxLayout()
        features_text = QLabel(
            "・エクセルの関数では実現が難しい複雑なデータ処理をAIが自動的に行います\n"
            "・具体的な例：\n"
            "  - 氏名を姓と名に分割する\n"
            "  - 文章の誤字脱字をチェックして修正する\n"
            "  - 文章を適切な表現に校正する\n"
            "  - 様々なフォーマットのデータを統一された形式に整える\n"
            "・一度ルールを作成すれば、同じパターンのデータを何度でも一括処理できます\n"
            "・CSVファイルを簡単に読み込んだり保存したりできます（Excel形式と互換性あり）"
        )
        features_text.setWordWrap(True)
        features_layout.addWidget(features_text)
        features_group.setLayout(features_layout)
        
        # 使い方の手順
        steps_group = QGroupBox("使い方の手順")
        steps_layout = QVBoxLayout()
        steps_text = QLabel(
            "1. **アプリを起動する**\n"
            "   - ExlAI.exeをダブルクリックして起動します\n\n"
            "2. **Gemini APIの無料APIキーを取得する**\n"
            "   - https://aistudio.google.com/app/apikey にアクセスして無料のAPIキーを作成できます\n"
            "   - 作成したAPIキーはアプリの「設定」メニューから入力してください\n\n"
            "3. **テンプレートを作成する**\n"
            "   - 上部の「テンプレート」エリアに例を入力します\n"
            "   - 1列目(A列)：AIに処理させたい元のデータを入力します\n"
            "   - 2列目以降(B列～)：AIに生成させたい項目の名前を入力します\n"
            "   - サンプルとなる入力と出力の例を最低1行入力してください\n\n"
            "4. **AIルールを生成する**\n"
            "   - 右側パネルの「テンプレートからルール生成」ボタンをクリックします\n"
            "   - しばらく待つと、AIがパターンを学習してルールを自動作成します\n\n"
            "5. **データを処理する**\n"
            "   - 下部の「データ入力エリア」（緑枠で囲まれた部分）に処理したいデータを入力します\n"
            "   - A列に元の値を入力します（コピー＆ペーストでOK）\n"
            "   - 「選択行だけ処理」または「未処理を一括処理」ボタンをクリックします\n"
            "   - AIが処理結果を各列に自動入力します\n\n"
            "6. **結果を保存する**\n"
            "   - メニューバーの「ファイル」→「CSV保存」を選択します\n"
            "   - 保存先を指定すれば完了です\n"
            "   - 最後に処理したデータは自動的にCSV形式でバックアップされており、メニューからいつでも開くことができます"
        )
        steps_text.setWordWrap(True)
        steps_layout.addWidget(steps_text)
        steps_group.setLayout(steps_layout)
        
        # 困ったときは？
        trouble_group = QGroupBox("困ったときは？")
        trouble_layout = QVBoxLayout()
        trouble_text = QLabel(
            "・処理に失敗した場合は「エラー」と表示されます\n"
            "・エラーが発生した際のポップアップ画面で「ログファイルを開く」ボタンを押すと詳細情報を確認できます\n"
            "・テンプレートを修正して「ルール再生成」ボタンを押せば、ルールを作り直すことができます\n"
            "・ルールを手動で編集したい場合は、履歴から選択して「詳細編集」ボタンをクリックしてください"
        )
        trouble_text.setWordWrap(True)
        trouble_layout.addWidget(trouble_text)
        trouble_group.setLayout(trouble_layout)
        
        # 注意点
        caution_group = QGroupBox("注意点")
        caution_layout = QVBoxLayout()
        caution_text = QLabel(
            "・Gemini APIキーは無料で使用できますが、入力データはGoogleの学習データとして使用される可能性があります\n"
            "・プライバシーやデータの機密性が重要な場合は、有料のAPIキーへの切り替えをご検討ください\n"
            "・処理の品質を高めたい場合は、設定から高性能なAIモデルに切り替えることができます"
        )
        caution_text.setWordWrap(True)
        caution_layout.addWidget(caution_text)
        caution_group.setLayout(caution_layout)
        
        # スクロールエリアにウィジェットを追加
        scroll_layout.addWidget(features_group)
        scroll_layout.addWidget(steps_group)
        scroll_layout.addWidget(trouble_group)
        scroll_layout.addWidget(caution_group)
        scroll_layout.addStretch()
        
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        basic_layout.addWidget(scroll_area)
        
        # 詳細情報タブ
        detail_tab = QWidget()
        detail_layout = QVBoxLayout(detail_tab)
        
        # テクニカル情報
        tech_info = QTextEdit()
        tech_info.setReadOnly(True)
        tech_info.setHtml("""
            <h2>開発者向け技術情報</h2>
            
            <h3>技術スタック</h3>
            <ul>
                <li><b>言語</b>: Python 3.x</li>
                <li><b>UI</b>: PySide6 (Qt for Python)</li>
                <li><b>AIエンジン</b>: Gemini API (google-genai)</li>
                <li><b>データ処理</b>: 標準CSV</li>
            </ul>
            
            <h3>プロジェクト構造</h3>
            <pre>
ExlAI
  ├── app/              # アプリケーションコード
  │   ├── services/     # APIやルール処理ロジック
  │   └── ui/           # UIコンポーネント
  ├── utils/            # ユーティリティ関数
  ├── doc/              # ドキュメント
  └── run_app.bat       # 起動スクリプト
            </pre>
            
            <h3>コアコンポーネント</h3>
            <ul>
                <li><b>integrated_ui.py</b>: メインウィンドウとパネル統合</li>
                <li><b>excel_panel.py</b>: エクセル風UIとデータテーブル</li>
                <li><b>ai_panel.py</b>: AIルール管理と処理操作</li>
                <li><b>rule_service.py</b>: ルール生成と適用ロジック</li>
            </ul>
        """)
        
        detail_layout.addWidget(tech_info)
        
        # タブの追加
        tab_widget.addTab(basic_tab, "基本的な使い方")
        tab_widget.addTab(detail_tab, "詳細情報")
        
        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.accept)
        close_button.setFixedWidth(100)
        
        # レイアウトに追加
        main_layout.addLayout(header_layout)
        main_layout.addWidget(tab_widget)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

if __name__ == "__main__":
    # テスト用コード
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = HelpDialog()
    dialog.exec() 