import requests
from telegram import Bot
from datetime import datetime
from pytz import timezone
import asyncio
from urllib.parse import quote
import logging
import re
import html

# تنظیمات پایه
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TOKEN = " "
CHANNEL_ID = "@Mazeruni_Xaver"

class WikipediaFetcher:
    def __init__(self):
        self.base_url = "https://mzn.wikipedia.org/w/api.php"
        self.month_names = [
            "ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن",
            "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"
        ]

    def _clean_html(self, text):
        """پاکسازی HTML از متن"""
        if not text:
            return ""
        # حذف تگ‌های HTML
        text = re.sub(r'<[^>]+>', '', text)
        # تبدیل entities به کاراکترهای عادی
        return html.unescape(text)

    def _convert_numbers(self, text):
        """تبدیل اعداد انگلیسی به فارسی"""
        persian_numbers = {
            '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
            '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
        }
        return ''.join(persian_numbers.get(c, c) for c in str(text))

    def _get_today_date_string(self):
        """ساخت رشته تاریخ امروز به فرمت مورد نیاز"""
        tehran = timezone('Asia/Tehran')
        now = datetime.now(tehran)
        return (
            f"{self._convert_numbers(now.day)}_"
            f"{self.month_names[now.month - 1]}_"
            f"{self._convert_numbers(now.year)}"
        )

    async def fetch_daily_page(self):
        """دریافت صفحه مربوط به تاریخ امروز"""
        date_str = self._get_today_date_string()
        page_title = f"پورتال:اسایی دکته‌ئون/دکته‌ئون_{date_str}"

        params = {
            'action': 'query',
            'format': 'json',
            'prop': 'extracts|info',
            'exintro': True,
            'explaintext': True,
            'titles': page_title,
            'inprop': 'url',
            'utf8': True
        }

        try:
            logger.info(f"در حال دریافت صفحه: {page_title}")
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            pages = data.get('query', {}).get('pages', {})
            if not pages or '-1' in pages:
                return None

            page_id = next(iter(pages))
            page_info = pages[page_id]

            return {
                'title': page_info.get('title'),
                'extract': self._clean_html(page_info.get('extract', '')),
                'url': f"https://mzn.wikipedia.org/wiki/{quote(page_info.get('title', ''))}"
            }

        except Exception as e:
            logger.error(f"خطا در دریافت داده: {str(e)}")
            return None

class TelegramBot:
    def __init__(self):
        self.bot = Bot(token=TOKEN)

    async def send_message(self, content):
        """ارسال پیام به تلگرام"""
        try:
            content = content[:4000] + "..." if len(content) > 4000 else content

            await self.bot.send_message(
                chat_id=CHANNEL_ID,
                text=content,
                disable_web_page_preview=True,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            logger.error(f"خطای تلگرام: {str(e)}")
            return False

async def main():
    """تابع اصلی اجرا"""
    wikifetcher = WikipediaFetcher()
    telegram_bot = TelegramBot()

    page_data = await wikifetcher.fetch_daily_page()
    if not page_data:
        content = (
            f"*⚠️ امروز وسه هَنتا هیچ خَوری نی‌یشتنه*\n\n"
            f"*شما توندی کسی بوئی که أمروز اخبار ره مازرونی زوون جه نویسنه*\n\n"
            f"[🔗 اینجه ره بزن و یاد بَی چتی‌ئه]({page_data.get('https://w.wiki/ENC6', 'https://w.wiki/ENC6')})"
        )
    else:
        content = (
            f"*📅 {wikifetcher._get_today_date_string().replace('_', ' ')}*\n\n"
            f"*📚 {page_data.get('extract', 'أمروز خور')}*\n\n"
            f"🔗 [منبع]({page_data.get('url', 'https://mzn.wikipedia.org')})\n"
            f"*🌐 @Mazeruni_Xaver*"
        )

    success = await telegram_bot.send_message(content)
    logger.info(f"پغوم راهی هاکردن {'موفق' if success else 'ناموفق'} بی‌یه")

if __name__ == "__main__":
    asyncio.run(main())
