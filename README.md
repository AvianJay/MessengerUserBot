# MessengerUserBot

🎉 一個 Python 套件，讓你輕鬆建立運行在 Messenger 的機器人！（類似 discord.py 的設計）

---

## 🚀 快速開始

### 安裝套件

```bash
git clone https://github.com/AvianJay/MessengerUserBot.git
cd MessengerUserBot/
pip install -e .
```

### 建立你的第一個機器人

```python
from messenger_userbot import MessengerBot

# 建立機器人實例
bot = MessengerBot(
    email='your_email@example.com',
    password='your_password',
    thread_id='your_thread_id'
)

# 定義訊息處理器
@bot.on_message
def handle_message(message):
    if message.sender.is_self():
        return
    
    if message.message == '!hello':
        bot.send_message(['Hello! 我是機器人！'])

# 登入並啟動
bot.login()
bot.run()
```

---

## 📦 套件結構

```
MessengerUserBot/
├── messenger_userbot/       # 主要套件
│   ├── __init__.py
│   ├── client.py           # MessengerBot 類別
│   ├── models.py           # MessengerUser, MessengerMessage 類別
│   └── utils.py            # 工具函數
├── examples/               # 範例機器人
│   ├── simple_bot.py      # 簡單範例
│   ├── bot_example.py     # 完整功能範例
│   └── README.md          # 範例說明
├── setup.py               # 套件安裝設定
└── README.md             # 本文件
```

---

## 🎯 使用範例

查看 [examples/](examples/) 資料夾：

- **simple_bot.py** - 基礎機器人範例，展示核心功能
- **bot_example.py** - 完整功能的機器人（原 main.py）

執行範例：

```bash
cd examples
python simple_bot.py
```

---

## 📖 核心功能

### MessengerBot 類別

主要的機器人客戶端：

```python
bot = MessengerBot(
    email='email',
    password='password',
    thread_id='thread_id',
    headless=False,
    use_wdm=True
)
```

### 訊息事件處理

使用 `@bot.on_message` 裝飾器註冊訊息處理函數：

```python
@bot.on_message
def my_handler(message):
    # message.sender - 發送者資訊 (MessengerUser)
    # message.message - 訊息內容
    # message.time - 時間戳記
    # message.reply - 回覆的訊息 (如果有)
    
    if '!ping' in message.message:
        bot.send_message(['Pong!'])
```

### 發送訊息

```python
# 發送文字訊息
bot.send_message(['Hello', 'World'])
bot.send_message('Single line message')

# 發送圖片
bot.send_image('path/to/image.jpg')
```

---

## 📄 說明

* **登入方式**：本專案基於 Web 自動化，使用 Selenium 模擬登入 Facebook 網頁版 Messenger
* **平台需求**：需安裝 Chrome 瀏覽器（ChromeDriver 會自動管理）
* **套件設計**：參考 discord.py 的 API 設計，提供簡潔易用的介面

---

## 🛠️ 注意事項

* 登入時可能需要手動驗證一次帳號
* 為避免帳號風險，建議使用副帳號運行此機器人
* 本專案僅供學術研究與個人使用，請勿用於違反 Facebook 使用條款的行為

---

## 💬 聯絡與貢獻

歡迎 PR 或 Issue，或透過 [GitHub](https://github.com/AvianJay) 聯繫作者！

~~(ChatGPT真好用)~~
