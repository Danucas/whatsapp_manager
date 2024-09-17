from uuid import uuid4
from wrapper import WebWhatsapp
import os
import time
import json
import threading
from psicologamarion import get_available_dates, get_available_hours, save_appointment, contact_info
from datetime import datetime
import traceback


thread_id = "567a16d4d88d418ab8c0103cad637f9d"

open_chats = {}  # -> "contact": "chat_id"

allowed_chats = ["Psicologa marion", "Mí Esposo", "test user"]

saved_chats = {"Psicologa marion": "2b2f16d4425d463391e3967c31f3de89"}


# Appointments Db manager


def get_appointment(user=None, id=None):
    appointments = get_appointments(user=user)
    appointment = [a for a in appointments if a.get("id") == id]
    if appointment:
        appointment = appointment[0]
    print("Get appointment:", appointment)
    return appointment


def insert_appointments(appointment):
    appointments = get_appointments()
    appointment["id"] = uuid4().hex[:8]
    appointments.append(appointment)
    with open("appointments.json", "w+") as appo_file:
        appo_file.write(json.dumps(appointments, indent=4))
    return appointment["id"]

def update_appointment(appointment_id, data, user=None):
    appointment: dict = get_appointment(user=user, id=appointment_id)
    appointment.update(data)

    appointments = get_appointments()
    index = 0
    for i, app in enumerate(appointments):
        if app.get("id") == appointment_id:
            index = i
            break

    appointments[index] = appointment

    with open("appointments.json", "w+") as appo_file:
        appo_file.write(json.dumps(appointments, indent=4))

    return appointment_id

def delete_appointment(appointment_id):
    appointments = get_appointments()
    index = 0
    for i, app in enumerate(appointments):
        if app.get("id") == appointment_id:
            index = i
            break
    del appointments[index]

    with open("appointments.json", "w+") as appo_file:
        appo_file.write(json.dumps(appointments, indent=4))


def get_appointments(user=None):
    if not os.path.exists("appointments.json"):
        appointments = []
    else:
        with open("appointments.json", "r") as appo_file:
            appointments = json.loads(appo_file.read())
    if user:
        appointments = [a for a in appointments if a.get("user") == user]
    return appointments


# Flows loader


def get_flows():
    with open("chat_flow.json", "r") as chat_flows:
        flows = json.loads(chat_flows.read())
        return flows


# Calculation functions


def availability(fecha: str = None, servicio: str = None, mes=None, semana=None, **kwargs):
    contact_info(kwargs.get("contact"))
    dia = fecha.split(" ")[1]
    hours = get_available_hours(servicio, dia, semana, mes)

    return {"horas": hours, "fecha": fecha, "servicio": servicio, "semana": semana, "mes": mes}


def appointment_list(contact: str = None, **kwargs):
    appointments = get_appointments(user=contact)

    return {
        "citas": [
            f'{a.get("fecha")} - {a.get("hora")} [{a.get("servicio")}] ({a.get("id")})'
            for a in appointments
        ]
    }


def create_appointment(
    fecha: str = None,
    hora: str = None,
    contact: str = None,
    servicio: str = None,
    id: str = None,
    **kwargs,
):
    if "." in hora:
        hora = hora.split(".")[1].strip()
    appointment = {
        "user": contact,
        "fecha": fecha,
        "hora": hora,
        "servicio": servicio,
        "modalidad": "online",
    }
    if not id:
        appo_id = insert_appointments(appointment)
    else:
        appo_id = update_appointment(id, {
            "fecha": fecha,
            "hora": hora
        })

    save_appointment(fecha=fecha, hora=hora, contact=contact, servicio=servicio, id=id, **kwargs)

    return {"id": appo_id}




def appointment_detail(text: str = None, contact: str = None, **kwargs):
    detail_id = text.split("(")
    if len(detail_id) > 1:
        detail_id = detail_id[1]
        detail_id = detail_id.split(")")[0]

    a = get_appointment(user=contact, id=detail_id)
    return {
        "detalle": f"{a.get('servicio')}\n{a.get('fecha')} - {a.get('hora')}\n({a.get('modalidad')})\nid: ({detail_id})",
        "id": detail_id,
        **a
    }


def appointment_update(id: str = None, **kwargs):
    return {"id": id, **kwargs}

def appointment_delete(id: str = None, **kwargs):
    return {"id": id, **kwargs}

def appointment_confirm_delete(id: str = None, **kwargs):
    delete_appointment(id)
    return {**kwargs}

def dates_availability(servicio: str = None, **kwargs):

    fechas, week, month = get_available_dates(
        servicio, week=kwargs.get("semana"), month=kwargs.get("mes")
    )

    return {
        "fechas": fechas,
        "semana": week,
        "mes": month,
        "servicio": servicio,
    }


def set_appointment_hour(
    hora: str = None,
    fecha: str = None,
    servicio: str = None,
    horas: list = None,
    **kwargs,
):
    return {"horas": horas, "servicio": servicio, "fecha": fecha, "hora": hora, **kwargs}


def increase_week(semana=None, **kwargs):
    if not semana:
        semana = 1
    semana = int(semana) + 1
    return dates_availability(semana=semana, **kwargs)

def decrease_week(semana=None, **kwargs):
    if not semana:
        semana = 1
    semana = int(semana) - 1
    if semana == 0:
        semana = 1
        if kwargs.get("month"):
            kwargs["month"] = kwargs["month"] - 1
    
    return dates_availability(semana=semana, **kwargs)


functions = {
    "therapist.availability": availability,
    "appointment.create": create_appointment,
    "appointments.list": appointment_list,
    "appointment.detail": appointment_detail,
    "appointment.update": appointment_update,
    "appointment.delete": appointment_delete,
    "appointment.confirm.delete": appointment_confirm_delete,
    "dates.availability": dates_availability,
    "set.hour": set_appointment_hour,
    "increase.week": increase_week,
    "decrease.week": decrease_week,
}


class ChatHistory:
    def __init__(
        self, chat_id=None, engine: WebWhatsapp = None, history_path="history"
    ):
        self.history_path = history_path
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
        if not os.path.exists(f"{self.history_path}"):
            os.mkdir(f"{self.history_path}")
        if not os.path.exists(f"{self.history_path}/{self.id}.json"):
            return []
        else:
            with open(f"{self.history_path}/{self.id}.json", "r") as history_file:
                return json.loads(history_file.read())

    def push_message(self, message) -> None:
        if not os.path.exists(f"{self.history_path}"):
            os.mkdir(f"{self.history_path}")
        history = self.history
        message["last_updated"] = str(datetime.now())
        history.append(message)
        with open(f"{self.history_path}/{self.id}.json", "w+") as history_file:
            history_file.write(json.dumps(history, indent=4))

    def process_message(self, message):
        self.push_message(message)
        print(f"process_message: From ( {message.get('contact')} )")
        return self.process_request()

    def process_option(
        self,
        flow_key=None,
        option=None,
        last_flow_key=None,
        last_flow=None,
        contact=None,
        command=None,
        next_flow_params=None,
    ):
        option_set = False
        # When the command refers to a selected option
        if not command in option.get("text")[:4]:
            return option_set, flow_key, next_flow_params
        else:
            flow_key = option.get("next")

            # Next Flow defined by the option selected
            if option.get("type") == "calculated":

                opt_func_key = option.get("function")
                opt_func = functions.get(opt_func_key)
                params = {}
                if option.get("params"):
                    params = {
                        k: v
                        for k, v in next_flow_params.items()
                        if k in option.get("params")
                    }
                if option.get("option_params"):
                    for param in option.get("option_params"):
                        option_param = option.get(param)
                        if "*" in option_param and "." in option_param:
                            option_param = (
                                option_param.replace("*", "").split(".")[1].strip()
                            )
                        if option.get("option_map"):
                            params[option.get("option_map")] = option_param
                        else:
                            params[param] = option_param

                params["contact"] = contact

                # Run calculated option function
                try:
                    result = opt_func(**params)
                except Exception as e:
                    if not opt_func_key or not opt_func:
                        raise Exception(
                            f"ERROR: Flow {last_flow_key}\nNo option.function found [{opt_func_key}]"
                        )
                    else:
                        raise e

                if option.get("output"):
                    for param in option.get("output"):
                        if result.get(param):
                            next_flow_params[param] = result[param]

            if last_flow.get("option_map") and option.get("type") != "calculated":
                next_flow_params[last_flow.get("option_map")] = (
                    option.get("text").replace("*", "").split(".")[1].strip()
                )

            if option.get("type") != "calculated" and option.get("output"):
                for k, out in option.get("output").items():
                    next_flow_params[k] = out

            option_set = True
        return option_set, flow_key, next_flow_params

    def proccess_flow(self, command=None, contact=None, history=None):
        """
        Proccess User message
        Get the last chatbot flow,
        """

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
        next_flow_params = None

        # Get last_flow configuration from last_chat_bot_message
        if last_chat_bot_message:
            last_flow_key = last_chat_bot_message.get("flow")
            last_flow = get_flows().get(last_flow_key)
            if not next_flow_params:
                next_flow_params = {}

            # Aggregate flow options from last params
            # Set flow -> option from the previuos saved chat params
            if last_chat_bot_message.get("params"):
                for k, v in last_chat_bot_message.get("params").items():
                    next_flow_params[k] = v
                if (
                    last_chat_bot_message.get("params", {}).get("options")
                    and last_flow.get("option_type") == "calculated"
                ):
                    last_flow["options"] = last_chat_bot_message.get("params", {}).get(
                        "options"
                    )

            if last_flow.get("options"):
                option_set = False
                for option in last_flow.get("options"):
                    option_set, flow_key, next_flow_params = self.process_option(
                        flow_key=flow_key,
                        option=option,
                        last_flow_key=last_flow_key,
                        last_flow=last_flow,
                        next_flow_params=next_flow_params,
                        contact=contact,
                        command=command,
                    )
                    if option_set:
                        break

                # Set the next flow_key if not option selected
                if not option_set:
                    flow_key = last_flow_key
                if last_flow.get("extra_options"):
                    print("extra options")
                    for option in last_flow.get("extra_options"):
                        option_set, flow_key, next_flow_params = self.process_option(
                            option=option,
                            last_flow_key=last_flow_key,
                            last_flow=last_flow,
                            flow_key=flow_key,
                            contact=contact,
                            command=command,
                            next_flow_params=next_flow_params,
                        )

            if last_flow.get("answer"):
                last_flow["options"] = None
                # If the flow requires to process user input use the defined function
                # in answer
                ans_func_key = last_flow.get("answer").get("function")
                ans_func = functions.get(ans_func_key)
                input_params = {}

                for param in last_flow.get("answer").get("input"):
                    if param in next_flow_params:
                        input_params[param] = next_flow_params[param]

                if last_flow.get("answer").get("map_command"):
                    # Insert command as mapped by answer type flow
                    input_params[last_flow.get("answer").get("map_command")] = command

                result = ans_func(contact=contact, **input_params)

                next_flow_payload = {}
                for param in last_flow.get("answer").get("output"):
                    next_flow_payload[param] = result[param]
                next_flow_params = next_flow_payload

                # Set the new flow from answer -> callback
                flow_key = last_flow.get("answer").get("callback")
                return

        return flow_key, next_flow_params

    def compose_message(self, flow, flow_key, next_flow_params):
        """
        Compose message using flow configuration and the results from the previuos flow
        """
        if not flow:
            print("No flow found for", flow_key)
            raise Exception("no flow found")
        chat_bot_message = flow.get("ask")
        chat_bot_options = flow.get("options")
        chat_bot_options_type = flow.get("option_type")
        extra_options = flow.get("extra_options")

        if flow.get("answer") and next_flow_params:
            next_flow_params["options"] = None

        # apply format using next_flow_params
        if next_flow_params:
            string_params = {}
            for k, param in [(k, v) for k, v in next_flow_params.items()]:
                if flow.get("params") and not k in flow.get("params"):
                    pass
                else:
                    # Aggregate options when flow options is null and
                    # and option_source is defined in the flow
                    if (
                        isinstance(param, list)
                        and not flow.get("option_source")
                        and flow.get("option_type") == "calculated"
                        and flow.get("option_function")
                    ):
                        raise Exception(
                            f"No option_source defined for calculated option flow {flow_key}"
                        )
                    if (
                        isinstance(param, list)
                        and flow.get("option_source")
                        and k == flow.get("option_source")
                    ):
                        string_params[k] = "\n".join(
                            [f"{i+1}. {p}" for i, p in enumerate(param)]
                        )
                        next_flow_params["options"] = []
                        for i, opt in enumerate(param):
                            option = {}
                            option["text"] = f"*{i+1}. {opt}*"
                            if not flow.get("callback"):
                                raise Exception(
                                    f"No callback found for flow {flow_key}"
                                )

                            option["next"] = flow.get("callback")

                            if flow.get("option_type"):
                                option["type"] = flow.get("option_type")
                                option["function"] = flow.get("option_function")
                                option["option_params"] = flow.get("option_params")
                                option["params"] = flow.get("input_params")
                                option["output"] = flow.get("option_response")
                                option["option_map"] = flow.get("option_map")
                            next_flow_params["options"].append(option)

                    else:
                        string_params[k] = param
            try:
                if (
                    next_flow_params
                    and "options" in next_flow_params
                    and not chat_bot_options
                ):
                    chat_bot_options = next_flow_params["options"]
                if not flow.get("options") and not chat_bot_options_type:
                    chat_bot_options = {}
                    next_flow_params["options"] = None
                    del next_flow_params["options"]
                chat_bot_message = chat_bot_message.format(**string_params)
            except Exception as e:
                print(f"chat_bot_message params: {string_params}")
                print(f"flow: {flow_key}\ntemplate: {chat_bot_message}")
                print(f"params: {json.dumps(next_flow_params, indent=4)}")
                raise e

        if chat_bot_options:
            chat_bot_message += "\n" + "\n".join(
                [op.get("text") for op in chat_bot_options]
            )

        if extra_options:
            chat_bot_message += "\n" + "\n".join(
                [op.get("text") for op in extra_options]
            )

        chat_bot_parsed_message = {
            "contact": "chatbot",
            "message": chat_bot_message,
            "flow": flow_key,
        }

        if next_flow_params:
            chat_bot_parsed_message["params"] = next_flow_params

        self.push_message(chat_bot_parsed_message)
        return chat_bot_message

    def process_request(self):
        history = self.history
        last_command = history[-1]
        contact = last_command.get("contact")
        command = last_command.get("message")

        if contact != "chatbot":
            # Proccess response from user and get config for the nex flow
            flow_key, next_flow_params = self.proccess_flow(
                command=command, contact=contact, history=history
            )

            # Create ChatBot message, and options
            # if not last_chat_bot_message:
            flow = get_flows().get(flow_key)

            # load the web.whatsapp.com url
            self.engine.check_whatsapp_status()

            self.engine.search_contact(contact)

            # Compose the message for the user
            # Take the input from chabot flow
            chat_bot_message = self.compose_message(flow, flow_key, next_flow_params)
            self.engine.send_whatsapp_message(chat_bot_message)

            # Use reload_whatsapp to prevent new messages to get unseen
            self.engine.close()


class ChatBot:
    def __init__(self, engine: WebWhatsapp, loop_timeout=10, history_path="history"):
        self.engine = engine
        self.engine.start_browser()
        self.active = self.engine.check_whatsapp_status()
        self.history_path = history_path
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
            chat = ChatHistory(
                chat_id=saved_chats.get(contact),
                engine=self.engine,
                history_path=self.history_path,
            )
            stories.append(chat.history)

        return stories

    def read_messages_loop(self):
        self.engine.open_whatsapp_web()
        while True:
            print("\rread_messages_loop at:", datetime.now(), end="")
            try:
                self.check_new_messages()

            except Exception as e:
                if not "No more messages..." in str(e):
                    print(traceback.format_exc())
                else:
                    print(e)
                    raise e
                break

            time.sleep(self.loop_timeout)

    def check_old_messages(self):
        for contact in allowed_chats:
            chat = ChatHistory(
                chat_id=saved_chats.get(contact),
                engine=self.engine,
                history_path=self.history_path,
            )
            chat.process_request()
        return {}

    def check_new_messages(self):
        # Get new messages from WebWhatsapp engine
        try:
            new_messages = self.engine.get_new_messages()
            if not new_messages:
                return
        except:
            self.engine.start_browser()
            self.start_service("agendar-citas")
            return self.check_new_messages()

        # Compare new_messages to match the "contact" for
        # any open_chats
        for message in new_messages:
            if any([contact in message.get("contact") for contact in allowed_chats]):
                open_chat_id = open_chats.get(message.get("contact"))
                open_chat = ChatHistory(
                    chat_id=open_chat_id,
                    engine=self.engine,
                    history_path=self.history_path,
                )
                open_chat.process_message(message)
                print(f"\n\t{self.history_path}/{open_chat.id}.json\n")
                open_chats[message.get("contact")] = open_chat.id

        return new_messages
