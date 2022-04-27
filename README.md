# Moffi SDK and tooling

## Installation

```bash
pip install -r requirements.txt
```

## Development

- Use black as formatter with line-length=120 option
- Use Pylint as linter

## SDK

All Moffi-related functions are under `moffi_sdk/`

See tooling files to get an example of usage

## Tooling
### Configuration

All tools can take this configuration on 3 way, by priority :
* From command line args (see `--help`)
* From `--config` command line argument
* From default config file located at `~/.config/moffi.ini`

### Moffics - Moffi to ICS proxy

moffics is a simple proxy for Moffi.io API that return the list of your in progress and future reservations as ICS Calendar

#### Run

```bash
python3 moffics.py -h
python3 moffics.py -l 0.0.0.0 -p 8888 -v
```

You should considerate use https reverse proxy like Caddy (https://caddyserver.com/)

#### Usage

##### With basicAuth

If your Webcal ics client support basicAuth, like ICSx⁵ (https://f-droid.org/fr/packages/at.bitfire.icsdroid/) for Android 

- Add a new Calendar to your API root endpoint `http://127.0.0.1:8888/` with basic authentication as your Moffi credentials

##### With a token

If your client does not support basicAuth
- Start Moffics with a secret key (32 random chars)
```bash
python3 moffics.py -s <my 32 chars secret key>
```
- Uses standard web client to request a token, using basicAuth
```bash
curl -u <moffi username> http://127.0.0.1:8888/getToken

{"token":"<my token>"}
```

- Add your calendar to your Webcal app with url `http://127.0.0.1:8888/token/<my token>`


### Simply order a desk

To order a desk for a given date

```bash
python order_desk.py -u <moffi username> -p <moffi password> -c <City where to book> -w <Workspace name> -d <Desk full name>
```
See Moffi web interface to find City, Workspace and Desk names


### Auto-Reservation

To order the same desk every possible days, up to 30 days

```bash
python auto_reservation.py -u <moffi username> -p <moffi password> -c <City where to book> -w <Workspace name> -d <Desk full name> -t <Date on isoformat>
```
See Moffi web interface to find City, Workspace and Desk names

It does not order a desk if there is already a reservation for a date, even if reservation is cancelled.
