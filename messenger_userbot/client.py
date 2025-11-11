"""
Main client for MessengerBot
"""
from selenium import webdriver
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys, ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
import pickle
import os
import threading
import json
from datetime import datetime
from .models import MessengerUser, MessengerMessage


class MessengerBot:
    """
    Main bot client for interacting with Facebook Messenger.
    
    Example usage:
        bot = MessengerBot(email='your_email', password='your_password')
        bot.login()
        
        @bot.on_message
        def handle_message(message):
            if message.message.startswith('!hello'):
                bot.send_message(['Hello!'])
        
        bot.run(thread_id='123456789')
    """
    
    def __init__(self, email=None, password=None, thread_id=None, headless=False, use_wdm=True, config=None):
        """
        Initialize the MessengerBot.
        
        Args:
            email: Facebook/Messenger email
            password: Facebook/Messenger password
            thread_id: Default thread ID to connect to
            headless: Run browser in headless mode
            use_wdm: Use webdriver-manager to manage ChromeDriver
            config: Optional dict with configuration (overrides individual params)
        """
        if config:
            self.config = config
        else:
            self.config = {
                'email': email,
                'password': password,
                'thread_id': thread_id,
                'headless': headless,
                'use_wdm': use_wdm
            }
        
        # Setup Chrome options
        opt = webdriver.ChromeOptions()
        opt.add_argument("--disable-notifications")
        opt.add_argument("--disable-gpu")
        opt.add_argument("--disable-accelerated-video")
        opt.add_argument("--disable-accelerated-video-encode")
        if self.config.get('headless', False):
            opt.add_argument("--headless")
        
        # Initialize driver
        if self.config.get('use_wdm', True):
            self.driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()), 
                options=opt
            )
        else:
            self.driver = webdriver.Chrome(options=opt)
        
        # Message handlers
        self._message_handlers = []
        self._sendmsg_limiter = threading.Semaphore(1)
        
    def on_message(self, func):
        """
        Decorator to register a message handler.
        
        Example:
            @bot.on_message
            def my_handler(message):
                print(f"Received: {message.message}")
        """
        self._message_handlers.append(func)
        return func
    
    def login(self, cookies_file='cookies.pkl'):
        """
        Login to Messenger using cookies or email/password.
        
        Args:
            cookies_file: Path to cookies file
        """
        print('Try to login...')
        if os.path.exists(cookies_file):
            print('Cookie Found. Login with cookie...')
            self.driver.get("https://www.messenger.com/")
            cookies = pickle.load(open(cookies_file, "rb"))
            for cookie in cookies:
                add = {'name': cookie['name'], 'value': cookie['value']}
                self.driver.add_cookie(add)
            if self.config.get('thread_id'):
                self.driver.get(f'https://www.messenger.com/t/{self.config["thread_id"]}')
        else:
            print('Cookie not found. Login with email and password...')
            self.driver.get("https://www.messenger.com/")
            time.sleep(2)
            ActionChains(self.driver) \
                .send_keys_to_element(self.driver.find_element(By.ID, "email"), self.config['email']) \
                .perform()
            ActionChains(self.driver) \
                .send_keys_to_element(self.driver.find_element(By.ID, "pass"), self.config['password']) \
                .perform()
            self.driver.find_element(By.CSS_SELECTOR, "span._2qcu").click()
            self.driver.find_element(By.ID, 'loginbutton').click()
            self.driver.implicitly_wait(5)
            input("Press Enter after login verification...")
            print('Saving cookie...')
            self.save_cookies(cookies_file)
    
    def save_cookies(self, cookies_file='cookies.pkl'):
        """Save current session cookies to file."""
        pickle.dump(self.driver.get_cookies(), open(cookies_file, "wb"))
    
    def send_message(self, msg_list):
        """
        Send a message to the current thread.
        
        Args:
            msg_list: String or list of strings to send
        """
        acquired = self._sendmsg_limiter.acquire()
        print("Sending Message")
        try:
            if isinstance(msg_list, str):
                msg_list = msg_list.strip().split("\n")
            try:
                textbox = self.driver.find_element(By.CSS_SELECTOR, '[aria-placeholder="Aa"]')
                textbox.click()
                for msg in msg_list:
                    textbox.send_keys(msg)
                    ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
                textbox.send_keys(Keys.ENTER)
            except Exception as e:
                print("Error sending message:", e)
        finally:
            if acquired:
                self._sendmsg_limiter.release()
    
    def send_image(self, filepath):
        """
        Send an image to the current thread.
        
        Args:
            filepath: Path to image file
        """
        upload = self.driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
        upload.send_keys(os.path.abspath(filepath))
        self.send_message([])
    
    def goto_thread(self, thread_id):
        """Navigate to a specific thread."""
        href_value = f'/t/{thread_id}/'
        self.driver.find_element(By.CSS_SELECTOR, f'a[href="{href_value}"]').click()
    
    def get_user_id(self, element):
        """Get user ID from an element."""
        button = element.find_element(By.XPATH, "../.")
        button.click()
        linkele = None
        link = None
        for i in range(10):
            try:
                menu = self.driver.find_element(By.CSS_SELECTOR, "[role=menu]")
                linkele = menu.find_element(By.CSS_SELECTOR, "a")
                link = linkele.get_attribute("href")
                break
            except:
                time.sleep(.2)
                continue
        if not link:
            return None
        try:
            button.click()
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            pass
        try:
            return int(link.split(".com/")[1].split("/")[0])
        except:
            return link.split(".com/")[1].split("/")[0]
    
    def _check_new_messages(self, latestmsg):
        """Internal method to check for new messages."""
        xpath = '/html/body/div[1]/div/div/div/div/div[2]/div/div/div[1]/div[1]/div/div[3]/div/div/div[1]/div/div/div/div/div/div[2]/div/div/div/div[1]/div/div/div/div/div/div/div/div[position()=last()]'
        xpathtyping = '/html/body/div[1]/div/div/div/div/div[2]/div/div/div[1]/div[1]/div/div[3]/div/div/div[1]/div/div/div/div/div/div[2]/div/div/div/div[1]/div/div/div/div/div/div/div/div[position()=last()-1]'
        
        text = ""
        reply = None
        
        try:
            baseele = self.driver.find_element(By.XPATH, xpath)
            if baseele.get_attribute("role") == "grid":
                baseele = self.driver.find_element(By.XPATH, xpathtyping)
            
            try:
                ele = baseele.find_element(By.CSS_SELECTOR, "div[dir=auto]")
                text = ele.text
                if not text:
                    ele = baseele.find_element(By.CSS_SELECTOR, "img[referrerpolicy=origin-when-cross-origin]")
                    src = ele.get_attribute("src")
                    if "emoji.php" in src:
                        text = ele.get_attribute("alt")
            except:
                ele = baseele.find_element(By.CSS_SELECTOR, "img[referrerpolicy=origin-when-cross-origin]")
                text = ele.get_attribute("src")
            
            lastm = [latestmsg[-1]]
            if len(latestmsg) > 1:
                lastm.append(latestmsg[-2])
            if baseele.id in lastm or text.startswith("blob:https://"):
                return latestmsg
            
        except:
            text = "無法獲取訊息"
            reply = None
        
        # Get sender info
        try:
            sender_element = None
            for _ in range(5):
                try:
                    sender_element = baseele.find_element(By.CSS_SELECTOR, 'img[style="border-radius: 50%;"]')
                    break
                except Exception:
                    time.sleep(0.05)
            if sender_element is None:
                raise Exception("Cannot find sender element")
            sender_name = sender_element.get_attribute('alt')
            userid = self.get_user_id(sender_element)
            sender_picture_url = sender_element.get_attribute('src')
        except Exception as e:
            print("Error getting sender info:", str(e))
            sender_name = "Unknown"
            sender_picture_url = ""
            userid = 0
        
        sender = MessengerUser(sender_name, sender_picture_url, userid)
        message = MessengerMessage(sender, text, reply=reply)
        
        if text != latestmsg[-1]:
            if text == "無法獲取訊息" and not message.sender.is_self():
                return latestmsg
            latestmsg.append(baseele.id)
            
            # Process message with handlers
            for handler in self._message_handlers:
                try:
                    threading.Thread(target=handler, args=(message,), daemon=True).start()
                except Exception as e:
                    print(f"Error in message handler: {e}")
        
        return latestmsg
    
    def run(self, thread_id=None):
        """
        Start the bot and begin listening for messages.
        
        Args:
            thread_id: Thread ID to monitor (uses config thread_id if not provided)
        """
        thread_id = thread_id or self.config.get('thread_id')
        if not thread_id:
            raise ValueError("thread_id must be provided either in config or as argument")
        
        print("Waiting for website to load...")
        self.driver.delete_all_cookies()
        
        while True:
            try:
                try:
                    self.driver.find_element(By.CSS_SELECTOR, "[aria-label=關閉]").click()
                    time.sleep(1)
                except:
                    pass
                try:
                    self.driver.find_element(By.CSS_SELECTOR, "[aria-label=不還原訊息]").click()
                except:
                    pass
                self.goto_thread(thread_id)
                break
            except Exception as e:
                time.sleep(1)
                pass
        
        time.sleep(5)
        print("Bot is running...")
        
        latestmsg = ["FIRST_TEMP_MESSAGE"]
        while True:
            time.sleep(.1)
            try:
                latestmsg = self._check_new_messages(latestmsg)
            except KeyboardInterrupt:
                print("Stopping bot...")
                self.driver.quit()
                break
            except Exception as e:
                print("Error:", str(e))
    
    def stop(self):
        """Stop the bot and close the browser."""
        self.driver.quit()
