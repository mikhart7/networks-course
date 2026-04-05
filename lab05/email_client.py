import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys



def send_email(from_addr, password, to_addr, subject, message, format_type="txt"):
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    
    if format_type == "html":
        msg.attach(MIMEText(message, "html"))
    else:
        msg.attach(MIMEText(message, "plain"))
    
    #SMTP_SSL (сразу защищенное соединение) на порту 465
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(from_addr, password)
        server.send_message(msg)
        print(f"Email sent to {to_addr}")
  
def main():
    if len(sys.argv) < 4:
        print("Usage: python email_client.py <from> <to> <subject> <message> [format]")
        sys.exit(1)
    
    from_addr = sys.argv[1]
    to_addr = sys.argv[2]
    subject = sys.argv[3]
    message = sys.argv[4]
    format_type = sys.argv[4] if len(sys.argv) > 4 else "txt"

    password=input("email_password:")
    
    send_email(from_addr, password, to_addr, subject, message, format_type)

if __name__ == "__main__":
    main()