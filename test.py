from chatbot import ChatBot
import os
import shutil


class TestEngine:
    """
    Selenium Test Wrapper to whatsapp ops
    """

    def __init__(self, nodeId, steps):
        """
        Defines the web selenium driver handler
        """
        self.steps = steps
        self.step_index = 0
        pass

    def remove_session(self, user):
        """
        Remove itself from browsers table
        """
        pass

    def registry_user(self):
        """
        Start a new Session and store cookies and LocalStorage
        """
        pass

    def start_browser(self):
        """
        Start the selenium Chrome driver
        """
        pass

    def restore_browser(self, executor_url, session_id):
        """
        Restart the selenium Firefox driver
        """
        pass
    

    def open_whatsapp_web(self):
        """
        Open the browser and search for the web whats app URL
        """
        pass

    def check_whatsapp_status(self):
        """
        check if the url is whatsapp, then waith for the content editable
        to be available
        """
        return True

    def auth(self):
        """
        Open web.whatsapp and checks for the QRcode canvas
        """
        pass

    def wait_registration(self):
        """
        Wait until the search input appear
        """
        pass

    def search_contact(self, contact_number):
        """
        Search for a number and click it to focus the messaging view
        Notes: replace this logic with a new one
        ---the browser should search the contact in the search bar at the left
        """
        pass

    def send_whatsapp_message(self, message):
        """
        Send a message to the contact focused by search_contact
        """
        pass

    def get_new_messages(self) -> list:
        """
        Return [
            {
                "contact": "x",
                "message": "Hello World!"
            }
        ]
        """
        try:
            message = self.steps[self.step_index]
            self.step_index += 1
            return [message]
        except:
            raise Exception("[MockWebWhatsappScrapper] No more messages...")
        
    def close(self):
        """
        Loads google
        """
        pass

    def save_screenshot(self, name="screenshot"):
        """
        Save a screenshot
        """
        pass

insert_appointment_steps = [
    {
        "contact": "test user",
        "message": "Hola"
    },
    {
        "contact": "test user",
        "message": "1"
    },
    {
        "contact": "test user",
        "message": "2"
    },
    {
        "contact": "test user",
        "message": "1"
    },
    {
        "contact": "test user",
        "message": "Septiembre 16"
    },
    {
        "contact": "test user",
        "message": "1"
    },
    {
        "contact": "test user",
        "message": "1"
    }

]

get_appointments_list = [
    {
        "contact": "test user",
        "message": "Hola"
    },
    # Select Servicios
    {
        "contact": "test user",
        "message": "1"
    },
    # Select Consulta Psicoterapia
    {
        "contact":"test user",
        "message":"1"
    },
    # Select Agendar Cita
    {
        "contact":"test user",
        "message":"1"
    },
    # Select First Date
    {
        "contact":"test user",
        "message":"1"
    },
    #Select First Hour 
    {
        "contact":"test user",
        "message":"1"
    },

]

if os.path.exists("test_history"):
    shutil.rmtree("test_history/")

# test_bot = ChatBot(TestEngine("test-engine", insert_appointment_steps), 1)
test_bot = ChatBot(TestEngine("test-engine", get_appointments_list), 1, history_path="test_history")


