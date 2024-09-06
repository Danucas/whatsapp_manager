from uuid import uuid4
from wrapper import WebWhatsapp
import os
import time
import json
import threading
from datetime import datetime


def get_flows():
    with open("chat_flow.json", "r") as chat_flows:
        flows = json.loads(chat_flows.read())
        return flows


thread_id = "567a16d4d88d418ab8c0103cad637f9d"


class ChatHistory:
    def __init__(self, chat_id=None, engine: WebWhatsapp=None):
        if not chat_id:
            self.chat_id = uuid4().hex
        else:
            self.chat_id = chat_id
        self.engine = engine
    
    @property
    def id(self):
        return self.chat_id
    
    @property
    def history(self):
        if not os.path.exists("history"):
            os.mkdir("history")
        if not os.path.exists(f"history/{self.id}.json"):
            return []
        else:
            with open(f"history/{self.id}.json", "r") as history_file:
                return json.loads(history_file.read())
    
    def push_message(self, message) -> None:
        if not os.path.exists("history"):
            os.mkdir("history")
        history = self.history
        history.append(message)
        with open(f"history/{self.id}.json", "w+") as history_file:
            history_file.write(json.dumps(history))
    
    def process_message(self, message):
        self.push_message(message)
        print(f"process_message: From ( {message.get('contact')} )")
        return self.process_request()
        
    def process_request(self):
        history = self.history
        last_command = history[-1]
        contact = last_command.get("contact")
        command = last_command.get("message")
        print("Processing Request", contact, command)

        if contact != "chatbot":
            

            # Get the last chatbot message
            last_chat_bot_message = None
            for h_index in range(len(history)):
                index = -(h_index + 1)
                chat = history[index]
                if chat.get("contact") == "chatbot":
                    last_chat_bot_message = chat
                    break
            
            # Set default flow to be menu-principal
            # if no last_chat_bot_message found
            flow_key = "menu-principal"

            # Look up command correlation with chat_flow from get_flows()
            if last_chat_bot_message:
                last_flow_key = last_chat_bot_message.get("flow")
                last_flow = get_flows().get(last_flow_key)

                if last_flow.get("options"):
                    option_set = False
                    for option in last_flow.get("options"):
                        if command in option.get("text"):
                            flow_key = option.get("next")
                            option_set = True
                    if not option_set:
                        flow_key = last_flow_key
                if last_flow.get("answer"):
                    ans_func_key = last_flow.get("answer").get("function")
                    print(ans_func_key)



            # if not last_chat_bot_message:

            flow = get_flows().get(flow_key)

            # load the web.whatsapp.com url
            self.engine.check_whatsapp_status()

            self.engine.search_contact(contact)
            chat_bot_message = flow.get("ask")
            if flow.get("options"):
                chat_bot_message += "\n" + "\n".join([op.get("text") for op in flow.get("options")])
            self.engine.send_whatsapp_message(chat_bot_message)
    
            # Use reload_whatsapp to prevent new messages to get unseen
            self.engine.close()

            self.push_message({
                "contact": "chatbot",
                "message": chat_bot_message,
                "flow": flow_key
            })
        






    



open_chats = {} # -> "contact": "chat_id"

allowed_chats = ["Psicologa marion", "Mí Esposo"]

saved_chats = {
    "Psicologa marion": "2b2f16d4425d463391e3967c31f3de89"
}

class ChatBot:
    def __init__(self, engine: WebWhatsapp, loop_timeout=10):
        self.engine = engine
        self.engine.start_browser()
        self.active = self.engine.check_whatsapp_status()
        self.loop_timeout = loop_timeout
        if self.active:
            self.start_service("agendar-citas")
    
    def start_service(self, service_name):
        if self.engine.check_whatsapp_status():
            thread = threading.Thread(target=self.read_messages_loop, args=())
            thread.start()
            self.active = True
            return True
        return False

    @property
    def history(self):
        stories = []
        for contact in allowed_chats:
            chat = ChatHistory(chat_id=saved_chats.get(contact), engine=self.engine)
            stories.append(chat.history)
        
        return stories
    

    def read_messages_loop(self):
        self.engine.open_whatsapp_web()
        while True:
            print("\rread_messages_loop at:", datetime.now(), end="")
            self.check_new_messages()
            time.sleep(self.loop_timeout)


    def check_old_messages(self):
        for contact in allowed_chats:
            chat = ChatHistory(chat_id=saved_chats.get(contact), engine=self.engine)
            chat.process_request()
        return {}
    
    def check_new_messages(self):
        # Get new messages from WebWhatsapp engine
        new_messages = self.engine.get_new_messages()

        # Compare new_messages to match the "contact" for
        # any open_chats
        for message in new_messages:
            if any([
                contact in message.get("contact")
                for contact in allowed_chats
            ]):
                open_chat_id = open_chats.get(message.get("contact"))
                open_chat = ChatHistory(chat_id=open_chat_id, engine=self.engine)
                open_chat.process_message(message)
                open_chats[message.get("contact")] = open_chat.id

        return new_messages
        




