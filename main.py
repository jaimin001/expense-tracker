import os.path
import re
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def extract_details(text):
    amount_pattern = r"Rs\.(\d+\.\d{2})"
    upi_pattern = r"to VPA ([\w.-]+@[\w.-]+)"
    date_pattern = r"on (\d{2}-\d{2}-\d{2})"
    reference_pattern = r"number is (\d+)"

    amount = re.search(amount_pattern, text)
    upi = re.search(upi_pattern, text)
    date = re.search(date_pattern, text)
    reference = re.search(reference_pattern, text)

    amount_value = amount.group(1) if amount else None
    upi_value = upi.group(1) if upi else None
    date_value = date.group(1) if date else None
    reference_value = reference.group(1) if reference else None

    return {
        "amount": amount_value,
        "upi": upi_value,
        "date": date_value,
        "reference_number": reference_value,
    }


def read_message(content) -> str:
    return content.get("snippet")


def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=52146)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        sender_email = "alerts@hdfcbank.net"
        current_date = datetime.now().strftime("%Y/%m/%d")
        query = f"from:{sender_email} after:{current_date}"

        results = service.users().messages().list(userId="me", q=query).execute()

        if "messages" in results:
            for message in results["messages"]:
                mail = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message["id"], format="full")
                    .execute()
                )
                message_body = read_message(mail)
                # print(message_body)
                print(extract_details(message_body))
        else:
            print("No transactions found")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
