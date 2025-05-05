import logging
from app.services.gemini_api import GeminiAPI, GeminiAPIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_generate_title():
    """テキストからタイトルを生成するテスト"""
    client = GeminiAPI()
    text = "山田太郎と鈴木花子が会議でプロジェクトの進捗について話し合った。"
    try:
        title = client.generate_title(text)
        print("Generated Title:", title)
    except GeminiAPIError as e:
        print("Error in generate_title:", e)


def test_summarize_minutes():
    """テキストから議事録を要約するテスト"""
    client = GeminiAPI()
    text = "山田: 進捗は順調です。鈴木: 来週までにレポートを提出します。"
    try:
        summary = client.summarize_minutes(text)
        print("Summarized Minutes:", summary)
    except GeminiAPIError as e:
        print("Error in summarize_minutes:", e)


if __name__ == "__main__":
    print("Testing generate_title...")
    test_generate_title()
    print("Testing summarize_minutes...")
    test_summarize_minutes() 