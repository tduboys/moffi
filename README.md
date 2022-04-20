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
python3 moffics.py -v
```

It listen to 8888 port

You should considerate use https reverse proxy like Caddy (https://caddyserver.com/)

## Usage

Use ICS application like ICSx⁵ (https://f-droid.org/fr/packages/at.bitfire.icsdroid/) for Android

Add a new Calendar to your API root endpoint with basic authentication as your Moffi credentials

Enjoy
