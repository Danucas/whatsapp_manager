#!/usr/bin/python3
"""
Selenium web driver used to send the QR code to the user
"""

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from PIL import Image
from io import BytesIO

# from api.v1.auth import send_email
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import os
import sys
import time
import traceback
import base64
import random
import shutil
import json

# import models.credentials as mc
from selenium.webdriver.common.keys import Keys

paths = os.environ.get("PATH").split(":")
exists = False
for pat in paths:
    if pat == "/opt/local/":
        exists = True
        break
if exists is False:
    os.environ["PATH"] = os.environ.get("PATH") + ":/usr/src/app/"
from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from pyvirtualdisplay import Display

print("Env:", os.environ["PATH"])


class Client:
    def __init__(self, id):
        self.instance_id = id

    def write_status(self, command, message):
        print("Command: ", command)
        print("Message: ", message)


class WebWhatsapp:
    """
    Selenium Wrapper to whatsapp ops
    """

    def __init__(self, nodeId, outData):
        """
        Defines the web selenium driver handler
        """
        self.instance = Client(nodeId)
        self.instance.write_status(
            "whatsapp_init", "Initializing Whatsapp messagging service"
        )
        self.out_data = outData
        self.node_id = nodeId
        self.last_giphy_search = ""
        self.remove_conf()
        self.remove_verify

    def remove_session(self, user):
        """
        Remove itself from browsers table
        """
        path = f"/usr/src/app/api/browsers"
        selenium = f"{path}/{self.instance.instance_id}.selenium"
        try:
            shutil.rmtree(selenium, ignore_errors=True)
            with open(f"{path}/table", "r") as tb_file:
                tb = json.loads(tb_file.read())
                for reg in tb.keys():
                    if tb[reg] == self.instance.instance_id:
                        del tb[reg]
                        break
            with open(f"{path}/table", "w") as table_w:
                table_w.write(json.dumps(tb))
        except Exception as e:
            return "remove failed"
        return "session removed"

    def registry_user(self):
        """
        Start a new Session and store cookies and LocalStorage
        """
        self.start_browser()

    def start_browser(self):
        """
        Start the selenium Chrome driver
        """
        op = Options()
        path = f"browsers/{self.instance.instance_id}.selenium"
        # op.add_argument('--headless')
        # op.add_argument('--no-sandbox')
        op.add_argument("--disable-dev-shm-usage")
        op.add_argument(f"user-data-dir={path}")
        op.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
        )

        chrome_path = "chromedriver-linux64/chromedriver"
        if not os.path.exists("browsers"):
            os.mkdir("browsers")
        try:
            service = Service(executable_path=chrome_path)
            self.driver = webdriver.Chrome(service=service, options=op)
        except:
            os.environ["PATH"] = os.environ["PATH"] + f":{chrome_path}"
            try:
                service = Service(executable_path=chrome_path)
                self.driver = webdriver.Chrome(service=service, options=op)
            except Exception as e:
                print(e)
                print(os.system("google-chrome-stable --version"))
                return
        b_name = self.driver.capabilities["browserName"]
        b_version = self.driver.capabilities["browserVersion"]
        print(f"Browser Version: {b_name} {b_version}")
        # --------------------------------------
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1080, 592)
        if not os.path.exists("running"):
            os.mkdir("running")
        with open(
            "running/{}.session".format(self.instance.instance_id), "w"
        ) as session_file:
            conf = {
                "session_id": str(self.driver.session_id),
                "url": str(self.driver.command_executor._url),
            }
            session_file.write(json.dumps(conf))

    def restore_browser(self, executor_url, session_id):
        """
        Restart the selenium Firefox driver
        """
        op = Options()
        op.headless = True
        op.set_preference("media.autoplay.default", 0)
        op.set_preference("media.mp4.enabled", True)

        self.driver = webdriver.Remote(
            command_executor=executor_url, desired_capabilities={}, options=op
        )
        self.driver.session_id = session_id
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1080, 592)
    

    def open_whatsapp_web(self):
        """
        Open the browser and search for the web whats app URL
        """
        print("Opening WhatsappWeb")
        retries = 1
        tries = 1
        while tries <= retries:
            try:
                self.driver.get("https://web.whatsapp.com")
                box_xpath = '//div[@contenteditable = "true"]'
                con_input_span = WebDriverWait(self.driver, 4).until(
                    EC.presence_of_all_elements_located((By.XPATH, box_xpath))
                )[0]
                return True
            except Exception as e:
                tries += 1
                time.sleep(2)
        return False

    def check_whatsapp_status(self):
        """
        check if the url is whatsapp, then waith for the content editable
        to be available
        """

        if not "web.whatsapp" in self.driver.current_url:
            self.driver.get("https://web.whatsapp.com")
        # print("check whatsapp web status")
        try:
            box_xpath = '//div[@contenteditable = "true"]'
            con_input_span = WebDriverWait(self.driver, 4).until(
                EC.presence_of_all_elements_located((By.XPATH, box_xpath))
            )[0]
            return True
        except Exception as e:
            pass
        return False

    def auth(self):
        """
        Open web.whatsapp and checks for the QRcode canvas
        """
        try:
            self.driver.get("https://web.whatsapp.com")
        except Exception as e:
            print(e)
            return False
        print("WebWhatsapp Auth")
        retries = 2
        tries = 0
        while tries < retries:
            try:
                canvas = WebDriverWait(self.driver, 4).until(
                    EC.presence_of_element_located((By.TAG_NAME, "canvas"))
                )
                print("auth: QR Code detected")
                location = canvas.location
                size = canvas.size
                qrcode = self.driver.get_screenshot_as_png()
                im = Image.open(BytesIO(qrcode))
                left = location["x"]
                top = location["y"]
                right = location["x"] + size["width"]
                bottom = location["y"] + size["height"]
                im = im.crop((left, top, right, bottom))
                if not os.path.exists("images"):
                    os.mkdir("images")
                im.save("images/{}.png".format(self.instance.instance_id))
                print("auth: QR Code saved")
                
                return True
            except TimeoutException:
                print("auth: Exception -> QR code not found")
                pass
            except Exception as e:
                print("\t", e)
                pass
            finally:
                tries += 1
                print(f"Retry {tries}/{retries}")
        return False

    def wait_registration(self):
        """
        Wait until the search input appear
        """
        box_xpath = '//div[@contenteditable = "true"]'
        max_retries = 2
        count = 1
        while max_retries <= count:
            try:
                print("Waiting register confirmation...")
                con_input_span = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, box_xpath))
                )[0]
                print("Session started")
                time.sleep(6)
                self.save_screenshot("init_page")
                return True
            except Exception as e:
                count += 1
                time.sleep(2)
                print("Confirmation Error: ", e)
                print(f"Retry {count}/{max_retries}")
        
        return False

    def search_contact(self, contact_number):
        """
        Search for a number and click it to focus the messaging view
        Notes: replace this logic with a new one
        ---the browser should search the contact in the search bar at the left
        """
        # self.save_screenshot(name='before_contacts')
        self.contact = contact_number
        box_xpath = '/html/body/div[1]/div/div/div[2]/div[3]/div/div[1]/div/div[2]/div[2]/div/div'
        max_retries = 20
        count = 0
        while True:
            try:
                print(f"search_contact: Searching {contact_number}")
                con_input_span = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, box_xpath))
                )[0]
                con_input = con_input_span.find_element(By.XPATH, "//p[contains(@class, 'selectable-text')]")
        
                con_input.click()
                con_input_span.click()
                print("search_contact: Contact found")
                con_input_span.send_keys(contact_number)
                con_input_span.send_keys(Keys.ENTER)
                time.sleep(2)
                self.instance.write_status(
                    "sending", "Sending message to {}".format(contact_number)
                )
                return
            except Exception as e:
                exp = traceback.format_exc()
                count += 1
                print("Selecting search input failed, trying again")
                print(exp)
                print(f"Retry {count}/{max_retries}")
                raise e

    def send_whatsapp_message(self, message):
        """
        Send a message to the contact focused by search_contact
        """

        # Focus the footer and store the input as msg_box
        try:
            print("send_whatsapp_message: Sending message")

            mss = message
            box_xpath = '/html/body/div[1]/div/div/div[2]/div[4]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div/p'

            for char in mss:    
                msg_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, box_xpath))
                )
                msg_box.send_keys(char)
            msg_box.send_keys(Keys.RETURN)
            time.sleep(2)
        except Exception as e:
            print(traceback.format_exc())
            raise e

    def get_new_messages(self) -> list:
        """
        Return [
            {
                "contact": "x",
                "message": "Hello World!"
            }
        ]
        """

        self.check_whatsapp_status()

        a = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[contains(@aria-label, 'unread')]"))
        )

        unread_messages = []
        
        for el in a:
            name = el.find_element(By.XPATH, '../../../../../div[1]')
            last_message = el.find_element(By.XPATH, '../../../../../div[2]')
            last_message = last_message.text.encode("utf-8").decode("utf-8").split("\n")[0]
            if last_message != "":
                unread_messages.append({
                    "contact": name.text.split("\n")[0],
                    "message": last_message
                })

        return unread_messages

    def close(self):
        """
        Loads google
        """
        try:
            self.driver.get("https://www.google.com/")
        except Exception as e:
            print(e)
            return False
        # self.driver.quit()

    def remove_conf(self):
        """
        Remove conf file from cache
        """
        file_src = "images"
        if not os.path.exists(file_src):
            os.mkdir(file_src)
        try:
            os.remove("{}/{}.conf".format(file_src, self.instance.instance_id))
        except Exception as e:
            print(
                "Warning: Can't remove png file {}.conf".format(
                    self.instance.instance_id
                ),
                e,
            )

    def remove_verify(self):
        """
        Remove verify png file from cache
        """
        file_src = "images"
        try:
            os.remove("{}/{}.png".format(file_src, self.instance.instance_id))
        except Exception as e:
            print("Can't remove png file {}.png".format(self.instance.instance_id), e)

    def remove_media(self):
        """
        Remove any saved gif or video for the instance
        """
        file_src = "./api/running/media/"
        list_dir = os.listdir(file_src)
        for direct in list_dir:
            if self.instance.instance_id in direct:
                try:
                    os.remove("{}/{}".format(file_src, direct))
                    print("media removed")
                except Exception as e:
                    print(
                        "Can't remove png file {}".format(self.instance.instance_id), e
                    )

    def save_screenshot(self, name="screenshot"):
        """
        Save a screenshot
        """
        if not os.path.exists("screenshots"):
            os.mkdir("screenshots")
        dirs = os.listdir("screenshots")
        shot = self.driver.get_screenshot_as_png()
        im = Image.open(BytesIO(shot))
        im.save("screenshots/{:0>4}-{}.png".format(len(dirs), name))
