# moffics - Moffi to ICS proxy

moffics is a simple proxy for Moffi.io API that return the list of your in progress and future reservations as ICS Calendar

## Installation

```bash
pip install -r requirements.txt
```

## Development

- Use black as formatter with line-length=120 option

## Run

```bash
python3 moffics.py -h
python3 moffics.py -l 0.0.0.0 -p 8888 -v
```

You should considerate use https reverse proxy like Caddy (https://caddyserver.com/)

## Usage

### With basicAuth

If your Webcal ics client support basicAuth, like ICSx⁵ (https://f-droid.org/fr/packages/at.bitfire.icsdroid/) for Android 

- Add a new Calendar to your API root endpoint `http://127.0.0.1:8888/` with basic authentication as your Moffi credentials

### With a token

If your client does not support basicAuth, you can start Moffics with a secret key (32 random chars)
```bash
python3 moffics.py -s <my 32 chars secret key>
```
Now, uses standard web client to request a token, using basicAuth
```bash
curl -u <moffi username> http://127.0.0.1:8888/getToken

{"token":"<my token>"}
```

You can now add your calendar to your Webcal app with url `http://127.0.0.1:8888/token/<my token>`

Enjoy
