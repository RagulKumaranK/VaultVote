import uuid
from datetime import datetime
import requests

from database import get_sms_settings, log_sms_notification, log_enrollment

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_SDK_AVAILABLE = True
except ImportError:
    TwilioClient = None
    TWILIO_SDK_AVAILABLE = False


def normalize_phone(mobile: str, country_code: str = '+91'):
    """
    Normalizes an input phone string into (E.164 format, 10-digit local format).
    Examples:
        '9876543210', '+91'   -> ('+919876543210', '9876543210')
        '+91 98765 43210'     -> ('+919876543210', '9876543210')
    """
    raw = str(mobile or '').strip()
    digits = ''.join(ch for ch in raw if ch.isdigit())
    cc = str(country_code or '+91').strip()
    if not cc.startswith('+'):
        cc = '+' + cc
    cc_digits = ''.join(ch for ch in cc if ch.isdigit())

    if not digits:
        return '', ''

    if raw.startswith('+'):
        local_10 = digits[-10:] if len(digits) >= 10 else digits
        return f'+{digits}', local_10

    if len(digits) == 10:
        return f'{cc}{digits}', digits

    if cc_digits and digits.startswith(cc_digits) and len(digits) == len(cc_digits) + 10:
        return f'+{digits}', digits[-10:]

    return f'{cc}{digits}', digits[-10:] if len(digits) >= 10 else digits


def mask_phone(mobile: str, country_code: str = '+91') -> str:
    """Returns a privacy-safe masked phone string such as '+91 XXXXXX3210'."""
    e164, local_10 = normalize_phone(mobile, country_code)
    if not local_10 or len(local_10) < 4:
        return 'XXXX'
    cc = str(country_code or '+91').strip()
    if not cc.startswith('+'):
        cc = '+' + cc
    if e164.startswith('+') and len(e164) > len(local_10) + 1:
        prefix = e164[: len(e164) - len(local_10)]
    else:
        prefix = cc
    masked_local = ('X' * max(len(local_10) - 4, 2)) + local_10[-4:]
    return f'{prefix} {masked_local}'


def generate_sms_receipt_ref() -> str:
    """Generates a compact confirmation reference code for the vote SMS."""
    date_part = datetime.now().strftime('%Y%m%d')
    short_hex = uuid.uuid4().hex[:6].upper()
    return f'VV-SMS-{date_part}-{short_hex}'


def build_vote_confirmation_message(
    voter_name: str,
    voter_id: str,
    timestamp: str,
    receipt_ref: str
) -> str:
    """
    Builds the ECI vote confirmation SMS text.
    Preserves secret-ballot privacy by omitting candidate choice while confirming voter identity and time.
    """
    clean_name = (voter_name or 'Voter').strip()
    return (
        f"VaultVote ECI Alert: Dear {clean_name} (Voter ID: {voter_id}), "
        f"your electronic vote was securely recorded on {timestamp}. "
        f"Receipt Ref: {receipt_ref}. Thank you for voting!"
    )


def _send_via_twilio(phone_e164: str, message_body: str, settings: dict):
    """Dispatches an SMS through Twilio SDK or Twilio REST API."""
    sid = settings.get('twilio_account_sid', '').strip()
    token = settings.get('twilio_auth_token', '').strip()
    from_num = settings.get('twilio_from_number', '').strip()

    if not sid or not token or not from_num:
        return False, '', 'Twilio credentials (Account SID, Auth Token, From Number) are incomplete.'

    try:
        if TWILIO_SDK_AVAILABLE and TwilioClient is not None:
            client = TwilioClient(sid, token)
            msg = client.messages.create(body=message_body, from_=from_num, to=phone_e164)
            return True, str(getattr(msg, 'sid', '') or ''), ''

        resp = requests.post(
            f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json',
            auth=(sid, token),
            data={'To': phone_e164, 'From': from_num, 'Body': message_body},
            timeout=6
        )
        payload = resp.json() if resp.content else {}
        if 200 <= resp.status_code < 300:
            return True, str(payload.get('sid', '')), ''
        return False, '', str(payload.get('message') or f'Twilio HTTP {resp.status_code}')
    except Exception as exc:
        return False, '', str(exc)


def _send_via_fast2sms(raw_10_digit: str, message_body: str, settings: dict):
    """Dispatches an SMS through the Fast2SMS v2 India REST API."""
    api_key = settings.get('fast2sms_api_key', '').strip()
    route = settings.get('fast2sms_route', 'q').strip() or 'q'

    if not api_key:
        return False, '', 'Fast2SMS API key is missing.'
    if len(raw_10_digit) != 10:
        return False, '', f'Fast2SMS requires a valid 10-digit Indian mobile number (got "{raw_10_digit}").'

    try:
        resp = requests.post(
            'https://www.fast2sms.com/dev/bulkV2',
            headers={'authorization': api_key, 'Content-Type': 'application/json'},
            json={
                'route': route,
                'message': message_body,
                'language': 'english',
                'flash': 0,
                'numbers': raw_10_digit
            },
            timeout=6
        )
        payload = resp.json() if resp.content else {}
        if 200 <= resp.status_code < 300 and payload.get('return') is True:
            req_id = str(payload.get('request_id', ''))
            return True, req_id, ''
        err_msg = payload.get('message') or f'Fast2SMS HTTP {resp.status_code}'
        if isinstance(err_msg, list):
            err_msg = '; '.join(str(x) for x in err_msg)
        return False, '', str(err_msg)
    except Exception as exc:
        return False, '', str(exc)


def _send_via_webhook(
    phone_e164: str,
    raw_10_digit: str,
    message_body: str,
    voter_id: str,
    receipt_ref: str,
    settings: dict
):
    """Dispatches an SMS payload via HTTP POST to a custom/Android SMS gateway webhook."""
    webhook_url = settings.get('webhook_url', '').strip()
    token = settings.get('webhook_token', '').strip()

    if not webhook_url:
        return False, '', 'Webhook SMS Gateway URL is missing.'

    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    try:
        resp = requests.post(
            webhook_url,
            headers=headers,
            json={
                'to': phone_e164,
                'phone': raw_10_digit,
                'message': message_body,
                'voter_id': voter_id,
                'receipt_ref': receipt_ref
            },
            timeout=6
        )
        if 200 <= resp.status_code < 300:
            req_id = ''
            try:
                body = resp.json()
                req_id = str(body.get('id') or body.get('message_id') or '')
            except Exception:
                pass
            return True, req_id, ''
        return False, '', f'Webhook returned HTTP {resp.status_code}: {resp.text[:180]}'
    except Exception as exc:
        return False, '', str(exc)


def dispatch_sms(
    phone: str,
    message_body: str,
    voter_id: str = 'SYSTEM',
    receipt_ref: str = '',
    is_testing: bool = False,
    force_live: bool = False,
    ip_address: str = '127.0.0.1'
) -> dict:
    """
    Sends an SMS notification using the configured gateway (Twilio, Fast2SMS, Webhook,
    or Simulation), persists the delivery audit record in sms_logs, and returns status metadata.
    Never raises exceptions so ballot casting cannot fail on third-party SMS outages.
    """
    settings = get_sms_settings()
    country_code = settings.get('country_code', '+91')
    provider = settings.get('provider', 'simulation').lower()
    phone_e164, raw_10 = normalize_phone(phone, country_code)
    masked = mask_phone(phone, country_code)
    ref = receipt_ref or generate_sms_receipt_ref()

    if not settings.get('enabled', True):
        return {
            'success': False,
            'delivered_live': False,
            'simulated': False,
            'status': 'DISABLED',
            'provider': provider.upper(),
            'masked_phone': masked,
            'phone_e164': phone_e164,
            'message_preview': message_body,
            'receipt_ref': ref,
            'provider_message_id': '',
            'error': 'SMS notifications are disabled in Admin Settings.',
            'log_id': None
        }

    if not phone_e164 or not raw_10:
        err = 'Voter mobile number is missing or invalid.'
        log_id = log_sms_notification(
            voter_id=voter_id,
            phone_number=str(phone or 'N/A'),
            message_body=message_body,
            provider=provider.upper(),
            status='FAILED',
            receipt_ref=ref,
            error_message=err
        )
        return {
            'success': False,
            'delivered_live': False,
            'simulated': False,
            'status': 'FAILED',
            'provider': provider.upper(),
            'masked_phone': masked,
            'phone_e164': phone_e164,
            'message_preview': message_body,
            'receipt_ref': ref,
            'provider_message_id': '',
            'error': err,
            'log_id': log_id
        }

    # Prevent accidental live SMS charges/spam to random numbers during test runs unless force_live=True
    use_simulation = (provider == 'simulation') or (is_testing and not force_live)

    if use_simulation:
        sim_id = f'SIM-{ref}'
        log_id = log_sms_notification(
            voter_id=voter_id,
            phone_number=phone_e164,
            message_body=message_body,
            provider='SIMULATION',
            status='SIMULATED',
            receipt_ref=ref,
            provider_message_id=sim_id
        )
        log_enrollment(
            voter_id=voter_id,
            action='SMS_CONFIRMATION_SIMULATED',
            details=f'Vote SMS notification logged (Simulation mode) for {masked}. Ref: {ref}',
            ip_address=ip_address
        )
        return {
            'success': True,
            'delivered_live': False,
            'simulated': True,
            'status': 'SIMULATED',
            'provider': 'SIMULATION',
            'masked_phone': masked,
            'phone_e164': phone_e164,
            'message_preview': message_body,
            'receipt_ref': ref,
            'provider_message_id': sim_id,
            'error': '',
            'log_id': log_id
        }

    _PROVIDER_DISPATCHERS = {
        'twilio': lambda p_e164, r_10, body, vid, r_ref, cfg: _send_via_twilio(p_e164, body, cfg),
        'fast2sms': lambda p_e164, r_10, body, vid, r_ref, cfg: _send_via_fast2sms(r_10, body, cfg),
        'webhook': lambda p_e164, r_10, body, vid, r_ref, cfg: _send_via_webhook(p_e164, r_10, body, vid, r_ref, cfg),
    }
    dispatcher = _PROVIDER_DISPATCHERS.get(provider)
    if dispatcher:
        ok, msg_id, err = dispatcher(phone_e164, raw_10, message_body, voter_id, ref, settings)
    else:
        ok, msg_id, err = False, '', f'Unsupported SMS provider: {provider}'

    status = 'SENT' if ok else 'FAILED'
    log_id = log_sms_notification(
        voter_id=voter_id,
        phone_number=phone_e164,
        message_body=message_body,
        provider=provider.upper(),
        status=status,
        receipt_ref=ref,
        provider_message_id=msg_id,
        error_message=err
    )
    log_enrollment(
        voter_id=voter_id,
        action=f'SMS_CONFIRMATION_{status}',
        details=(
            f'Vote confirmation SMS delivered via {provider.upper()} to {masked} (Ref: {ref}).'
            if ok else
            f'Vote confirmation SMS via {provider.upper()} to {masked} failed: {err}'
        ),
        ip_address=ip_address
    )

    return {
        'success': ok,
        'delivered_live': ok,
        'simulated': False,
        'status': status,
        'provider': provider.upper(),
        'masked_phone': masked,
        'phone_e164': phone_e164,
        'message_preview': message_body,
        'receipt_ref': ref,
        'provider_message_id': msg_id,
        'error': err,
        'log_id': log_id
    }


def send_vote_confirmation_sms(
    receipt: dict,
    voter_mobile: str,
    ip_address: str = '127.0.0.1',
    is_testing: bool = False,
    force_live: bool = False
) -> dict:
    """Formats and sends the post-vote SMS notification to the voter's registered phone number."""
    receipt_ref = generate_sms_receipt_ref()
    message_body = build_vote_confirmation_message(
        voter_name=receipt.get('voter_name', 'Voter'),
        voter_id=receipt.get('voter_id', ''),
        timestamp=receipt.get('timestamp', ''),
        receipt_ref=receipt_ref
    )
    return dispatch_sms(
        phone=voter_mobile,
        message_body=message_body,
        voter_id=receipt.get('voter_id', ''),
        receipt_ref=receipt_ref,
        is_testing=is_testing,
        force_live=force_live,
        ip_address=ip_address
    )
