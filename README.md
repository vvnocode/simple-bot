# Telegram Bot

一个基于 python-telegram-bot 的 Telegram 机器人。

## 安装部署

### 1. 环境准备
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

修改 `tgbot.py` 中的配置项：
- `TELEGRAM_TOKEN`: 从 @BotFather 获取的机器人令牌
- `CHAT_ID`: 目标频道或群组的 ID
- `KEYWORDS`: 关键词列表，用于过滤帖子

### 3. 运行

#### 方式一：直接运行（开发测试用）
```bash
./start.sh
```

#### 方式二：后台运行（推荐）
```bash
# 启动
nohup ./start.sh > bot.log 2>&1 &

# 查看进程
ps aux | grep tgbot.py

# 查看日志
tail -f bot.log

# 停止运行
pkill -f tgbot.py
# 或者用进程ID关闭
kill <进程ID>
```

## 注意事项

1. 确保服务器能访问 Telegram API
2. 建议定期检查日志确保运行正常
3. 如遇到问题，查看 bot.log 日志文件

## 许可证

[MIT](LICENSE)