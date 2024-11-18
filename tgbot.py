#!/usr/bin/env python3
import logging
import time
from datetime import datetime
from collections import OrderedDict
import feedparser
from telegram.ext import ApplicationBuilder, CommandHandler
import asyncio

# Basic config
TELEGRAM_TOKEN = ''
CHAT_ID = ''
KEYWORDS = ['pqs', '港仔', 'boil']
OFFICIAL_ID = 'CLAWCLOUD-VPS'
CHECK_INTERVAL = 30
CACHE_DURATION = 24 * 3600  # 24小时的缓存时间

# RSS配置
RSS_FEEDS = {
    'NodeSeek': 'https://rss.nodeseek.com',
    'V2EX': 'https://www.v2ex.com/index.xml'
}

# 消息缓存，使用OrderedDict来限制缓存大小
MESSAGE_CACHE = OrderedDict()
MAX_CACHE_SIZE = 1000

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

def clean_cache():
    """清理过期的缓存"""
    current_time = time.time()
    expired_keys = [k for k, (t, _) in MESSAGE_CACHE.items() 
                   if current_time - t > CACHE_DURATION]
    for k in expired_keys:
        MESSAGE_CACHE.pop(k)

def is_message_sent(message_key):
    """检查消息是否已经发送过"""
    clean_cache()
    return message_key in MESSAGE_CACHE

def mark_message_sent(message_key):
    """标记消息为已发送"""
    if len(MESSAGE_CACHE) >= MAX_CACHE_SIZE:
        MESSAGE_CACHE.popitem(last=False)  # 移除最旧的项目
    MESSAGE_CACHE[message_key] = (time.time(), True)

def parse_feed_entry(entry, source):
    """解析单个Feed条目"""
    title = entry.title.strip()
    link = entry.link
    
    # 统一处理发布时间
    published_time = None
    if hasattr(entry, 'published_parsed'):
        published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
    elif hasattr(entry, 'updated_parsed'):
        published_time = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
    else:
        published_time = datetime.now()

    return {
        'title': title,
        'link': link,
        'time': published_time,
        'forum': source
    }

def parse_rss_feed():
    """解析RSS订阅"""
    official_posts = []
    user_posts = []

    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            
            if feed.status != 200:
                logger.warning(f"{source} RSS返回状态码: {feed.status}")
                continue
                
            for entry in feed.entries:
                # 检查标题是否包含关键词
                title = entry.title.strip()
                if not any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                    continue

                # 生成消息唯一键
                message_key = f"{source}:{entry.link}"
                if is_message_sent(message_key):
                    continue

                post_info = parse_feed_entry(entry, source)
                
                # NodeSeek的官方帖子特殊处理
                if source == 'NodeSeek' and hasattr(entry, 'author') and entry.author == OFFICIAL_ID:
                    official_posts.append(post_info)
                else:
                    user_posts.append(post_info)

                mark_message_sent(message_key)

        except Exception as e:
            logger.error(f"{source} RSS解析错误: {str(e)}")
            continue

    return official_posts, user_posts

async def send_telegram_message(bot, post, is_official=False):
    """发送Telegram消息"""
    linked_title = f'<a href="{post["link"]}">{post["title"]}</a>'
    
    source_emoji = {
        'NodeSeek': '🔍',
        'V2EX': '💡'
    }.get(post['forum'], '📢')
    
    if is_official:
        message = (
            f"🚨 <b>爪云官方通知 {source_emoji}</b>\n\n"
            f"🔔 来源：{post['forum']}\n"
            f"📎 标题：{linked_title}"
        )
    else:
        message = (
            f"🔔 来源：{post['forum']}\n"
            f"💬 标题：{linked_title}"
        )
    
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        await asyncio.sleep(3)  # 增加到3秒间隔
    except Exception as e:
        logger.error(f"消息发送错误: {str(e)}")

async def check_feed(bot):
    """检查RSS订阅"""
    try:
        official_posts, user_posts = parse_rss_feed()
        
        for post in official_posts:
            await send_telegram_message(bot, post, is_official=True)
        for post in user_posts:
            await send_telegram_message(bot, post, is_official=False)
            
    except Exception as e:
        logger.error(f"订阅检查错误: {str(e)}")

async def periodic(bot):
    """定期执行检查"""
    while True:
        await check_feed(bot)
        await asyncio.sleep(CHECK_INTERVAL)

def start(update, context):
    """启动命令处理"""
    update.message.reply_text(
        '🤖 监控机器人已启动！\n\n'
        '📡 正在监控以下RSS订阅：\n'
        '🔍 NodeSeek\n'
        '💡 V2EX\n\n'
        '⚡ 机器人已开始工作...'
    )

def status(update, context):
    """状态命令处理"""
    status_text = "🤖 RSS监控状态报告：\n\n"
    for source, url in RSS_FEEDS.items():
        source_emoji = {
            'NodeSeek': '🔍',
            'V2EX': '💡'
        }.get(source, '📢')
        status_text += f"{source_emoji} {source} RSS: {url}\n"
    status_text += f"\n⏱️ 检查间隔：{CHECK_INTERVAL}秒\n"
    status_text += f"📦 缓存数量：{len(MESSAGE_CACHE)}/{MAX_CACHE_SIZE}\n"
    status_text += f"🔄 系统运行正常"
    
    update.message.reply_text(status_text)

def main():
    """主函数"""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    
    # 创建事件循环
    loop = asyncio.get_event_loop()
    
    # 创建并运行后台任务
    loop.create_task(periodic(application.bot))
    
    # 启动机器人
    application.run_polling()

if __name__ == '__main__':
    main()
