import requests
import calendar
from datetime import datetime, timedelta
import os
import uuid
import json


API_KEY = "9f71b0ebfe3f4d29a3e2f7c895018e907089c97b0d5745eda3f8a11c1b3e4b3f"


def get_week_at_month(week, month):
    day = datetime.now()
    if not month:
        month = day.strftime("%m")

    if not str(month).isnumeric():
        month = datetime.strptime(f"{month}/{day.year}", "%B/%Y").month

    month = int(month)
    if not week:
        for w_i, w in enumerate(calendar.monthcalendar(day.year, month)):
            if day.day in w:
                week = w_i + 1
                return week, month, day.year

    else:
        if week > len(calendar.monthcalendar(day.year, month)):
            week = 1
            month += 1
        if month > 12:
            month = 1
        return week, month, day.year


def get_days_at_week(week, month):
    week, month, year = get_week_at_month(week, month)
    print(f"week {week - 1} at month {month}", week, month, year)
    week_days = calendar.monthcalendar(2024, month)[week - 1]
    print(week_days)

    day_string = f"{week_days[0]}/{month}/{year}"

    dt = datetime.strptime(day_string, "%d/%m/%Y")

    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)

    today = datetime.now()
    if start < today:
        start = today + timedelta(days=1)

    return [date for date in range(start.day, end.day)], week, month, year


def available_hours_at_day(day, week=None, month=None, service=None, therapist=None):
    params = {
        "therapist": "6659e5864704294af8e28cb6",
        "day": day,
        "month": month,
        "year": 2024,
        "timezone": "America/Bogota",
    }
    response = requests.get(
        "http://localhost:5000/api/v1/appointments/availability",
        headers={"Api-Key": API_KEY},
        params=params,
    )
    print("availability:", response, params)

    if response.status_code == 200:
        data = response.json().get("response")
        hours = [h.get("time") for h in data]
        return hours
    return []


def get_available_dates(
    service,
    therapist=None,
    week: str = None,
    month: str = datetime.now().strftime("%B"),
):
    dates = []
    days, week, month, year = get_days_at_week(week, month)
    for day in days:
        hours = available_hours_at_day(
            day, week=week, month=month, service=service, therapist=therapist
        )

        if not hours:
            continue
        else:
            m_string = datetime.strptime(str(month), "%m").strftime("%B")
            dates.append(f"{m_string} {day}")
    return dates, week, month


def get_available_hours(service, day, week, month):
    hours = available_hours_at_day(day=day, week=week, month=month)
    return hours


SERVICE_MAP = {
    "terapia-psicologica": "04f02642f91d41f2b532491d",
    "constelacion-individual": "9e050bcd391d4e518c475606",
}


def save_appointment(
    fecha: str = None,
    hora: str = None,
    contact: str = None,
    servicio: str = None,
    id: str = None,
    **kwargs,
):
    url = "http://localhost:5000/api/v1/appointments"
    # si el id es none el metodo es "POST" y si hay una id es "PUT"
    headers = {
        "Content-Type": "application/json",
        "Source-App": "chatbot",
        "Contact": contact,
        "Api-Key": API_KEY
    }

    date = datetime.strptime(f"{fecha} 2024", "%B %d %Y")
    body = {
        "service_id": SERVICE_MAP.get(servicio),
        "date": {
            "day": date.day,
            "month": date.month,
            "year": date.year,
            "weekDay": date.weekday(),
        },
        "plan": 1,
        "location": "online",
        "time": hora,
        "timezone": "America/Bogota",
        "_id": id,
        "pack_id": None,
        "cupon_id": None,
    }

    print("peticion crear citas", url, headers, body)

    pass


def get_users():
    if not os.path.exists("users.json"):
        return {}
    else:
        with open("users.json", "r") as users_file:
            return json.loads(users_file.read())


def get_user(contact):
    users = get_users()
    user = users.get(contact)
    if not user:
        create_user(contact)
    return get_users().get(contact)


def create_user(contact):
    users = get_users()
    if not contact in users.keys():
        users[contact] = {
            "contact": contact,
            "email": f"{uuid.uuid4().hex[:10]}@mail.com"
        }
        with open("users.json", "w+") as users_file:
            users_file.write(json.dumps(users, indent=4))
    



def contact_info(contact):
    user = get_user(contact)
    url = "http://localhost:5001/api/v1/users/info"
    headers = {
        "Api-Key": API_KEY,
        "Content-Type": "application/json",
        "User": json.dumps({"userinfo":{"email":user.get("email")}})
    }

    response = requests.get(url,headers=headers)

    if response.status_code == 200:
        return response.json().get("response")
    else:
        return create_user_in_backend(contact)
    print("contact info request", headers)

def create_user_in_backend(contact):
    user = get_user(contact)
    url = "http://localhost:5001/api/v1/users"
    headers = {
        "Api-Key": API_KEY,
        "Content-Type": "application/json",
        "User": json.dumps({"userinfo":{"email":user.get("email")}})
    }
    response = requests.post(url, headers=headers, json={})
    if response.status_code == 202:
        return contact_info(contact)

