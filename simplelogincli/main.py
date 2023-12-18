import argparse
import requests
import getpass
import time
BASE_URL = "https://app.simplelogin.io"
API_KEY_FILE = "api_key.txt"
USER_EMAIL_FILE = "user_email.txt"
def save_user_email(email):
    with open(USER_EMAIL_FILE, "w") as file:
        file.write(email)
def load_user_email():
    try:
        with open("user_email.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        print("User email file 'user_email.txt' not found.")
        return None
    
def save_api_key(api_key):
    with open(API_KEY_FILE, "w") as file:
        if isinstance(api_key, tuple):
            api_key = api_key[0]
        file.write(api_key)

def load_api_key():
    try:
        with open(API_KEY_FILE, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None
    
def login(email, password, device):
    api_key = load_api_key()
    user_email = load_user_email()
    if api_key and user_email:
        return api_key, user_email
    url = f"{BASE_URL}/api/auth/login"
    data = {"email": email, "password": password, "device": device}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        api_key = response.json().get("api_key")
        if api_key:
            save_api_key(api_key)
            save_user_email(email)
            return api_key, email
        else:
            print("API key not found in the response.")
    elif response.status_code == 403:
        print("User has enabled FIDO. Please use the API Key instead.")
    else:
        print(f"Login failed. Status code: {response.status_code}")
        print(response.json().get("error", "Unknown error"))
    return None, None

def account_details(api_key):
    url = f"{BASE_URL}/api/user_info"
    headers = {"Authentication": api_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user_info = response.json()
        print(f"User: {user_info['name']}")
        print(f"Premium: {user_info['is_premium']}")
    else:
        print(f"Failed to get user info. Status code: {response.status_code}")
        return None


def view_aliases(api_key, page_id=0):
    url = f"{BASE_URL}/api/v2/aliases"
    headers = {"Authentication": api_key}
    params = {"page_id": page_id}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        aliases = response.json().get("aliases", [])
        print("User aliases:")
        for alias in aliases:
            print(f"Alias ID: {alias['id']}")
            print(f"Email: {alias['email']}")
            print(f"Creation Date: {alias['creation_date']}")
            print(f"Enabled: {alias['enabled']}")
            print(f"Mailbox: {alias['mailbox']['email']}")
            print(f"Note: {alias['note']}")
            print(f"Pinned: {alias['pinned']}")
            print(f"Support PGP: {alias['support_pgp']}")
            print("-" * 30)
    else:
        print(f"Failed to get aliases. Status code: {response.status_code}")
        print(response.json().get("error", "Unknown error"))

def create_alias(api_key, user_email):
    alias_prefix_signed_suffix = input("Enter alias prefix and signed suffix (e.g., test123): ")
    default_mailbox_address = user_email
    try:
        with open("user_email.txt", "r") as file:
            mailbox_address = file.read().strip()
    except FileNotFoundError:
        print(f"Error: File 'user_email.txt' not found.")
        return
    mailbox_address = input(f"Enter mailbox address (default: {default_mailbox_address}): ") or default_mailbox_address
    mailbox_id = get_mailbox_id(api_key, mailbox_address)
    if not mailbox_id:
        print(f"Error: Mailbox not found for address '{mailbox_address}'")
        return
    url = f"{BASE_URL}/api/v3/alias/custom/new"
    headers = {"Authentication": api_key}
    data = {
        "alias_prefix": alias_prefix_signed_suffix,
        "signed_suffix": "",
        "mailbox_ids": [mailbox_id],
        "note": None,
        "name": None
    }
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            new_alias_info = response.json()
            print("New custom alias created successfully:")
            print(new_alias_info)
            break
        elif response.status_code == 412 and "Alias creation time is expired" in response.json().get("error", ""):
            print("Alias creation time is expired, retrying...")
        else:
            print(f"Failed to create custom alias. Status code: {response.status_code}")
            print(response.json().get("error", "Unknown error"))
            retry_count += 1
        time.sleep(2)
    if retry_count == max_retries:
        print("Max retry attempts reached. Alias creation failed.")

def get_mailbox_id(api_key, mailbox_address):
    url = f"{BASE_URL}/api/v2/mailboxes"
    headers = {"Authentication": api_key}
    params = {"email": mailbox_address}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        mailboxes = response.json().get("mailboxes", [])
        if mailboxes:
            return mailboxes[0]["id"]
        else:
            return None
    else:
        print(f"Failed to get mailbox ID. Status code: {response.status_code}")
        print(response.json().get("error", "Unknown error"))
        return None


def main():
    parser = argparse.ArgumentParser(description="SimpleLogin CLI Tool")
    parser.add_argument("command", choices=[
        "login", "account_details", "view_aliases", "create_alias"
    ], help="Command to execute")
    parser.add_argument("--email", help="User email")
    parser.add_argument("--password", help="User password")
    parser.add_argument("--device", help="Device name")
    parser.add_argument("--hostname", help="Hostname for certain commands")
    parser.add_argument("--mode", help="Mode for create_random_alias command")
    parser.add_argument("--note", help="Note for certain commands")
    parser.add_argument("--page_id", type=int, help="Page ID for paginated requests")
    parser.add_argument("--pinned", action="store_true", help="Filter for pinned aliases")
    parser.add_argument("--disabled", action="store_true", help="Filter for disabled aliases")
    parser.add_argument("--enabled", action="store_true", help="Filter for enabled aliases")
    parser.add_argument("--query", help="Query parameter for certain commands")
    args = parser.parse_args()
    page_id = getattr(args, 'page_id', 0)
    if args.command == "login":
        api_key = load_api_key()
        if not api_key:
            email = args.email or input("Enter your email: ")
            password = args.password or getpass.getpass("Enter your password: ")
            device = args.device or input("Enter a device name: ")
            api_key = login(email, password, device)
        if api_key:
            print(f"Logged in with API key: {api_key}")
            save_api_key(api_key)
    elif args.command == "account_details":
        api_key = load_api_key()
        if api_key:
            account_details(api_key)
        else:
            print("API key not found. Please log in first.")
    elif args.command == "view_aliases":
        api_key = load_api_key()
        if api_key:
            page_id = args.page_id if args.page_id is not None else 0
            view_aliases(api_key, page_id)
        else:
            print("API key not found. Please log in first.")
    elif args.command == "create_alias":
        api_key = load_api_key()
        if api_key:
            # Load user's email from the file
            user_email = load_user_email()
            if not user_email:
                print("User email not found. Please log in first.")
                return
            create_alias(api_key, user_email)
        else:
            print("API key not found. Please log in first.")

if __name__ == "__main__":
    main()
