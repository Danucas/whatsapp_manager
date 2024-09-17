WhatsApp API


Authentication process

/auth:
response: {
    qrcode: "<codeurl>",
    verification_url: "<url to verify authentication>"
}

/qrcode/<unique identifier>
return qrcode image in png format




## Start the service

install requirements

``` bash
pip install -r requirements.txt
```


Start the API Service

``` bash
python3 app.py
```


AGREGAR link para abrir perfil desde whatsapp
