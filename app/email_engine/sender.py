from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.config import SENDGRID_API_KEY


def send_email_raw(from_email: str, to_email: str, subject: str, body: str) -> None:
    """Send a plain-text email via SendGrid."""
    if not SENDGRID_API_KEY:
        raise ValueError("SENDGRID_API_KEY environment variable not set")

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=body,
    )

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    print(f"Sent to {to_email} (status={response.status_code})")


def send_email(to_email, recruiter_name, company, job_title, job_link):
    subject = f"Interest in {job_title} opportunity at {company}"

    body = f"""
Hi {recruiter_name},

I noticed that {company} is currently hiring for the role of {job_title}.

My background includes infrastructure automation, cloud operations, production systems, and reliability engineering, and I believe my experience aligns well with the role.

I would greatly appreciate the opportunity to connect regarding this opening:
{job_link}

Thank you for your time and consideration.

Best regards
Your Name
Your LinkedIn
Your Contact
"""

    message = Mail(
        from_email='your_verified_sender@example.com',
        to_emails=to_email,
        subject=subject,
        plain_text_content=body
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        print(f"Sent to {to_email}")
        print(response.status_code)

    except Exception as e:
        print(f"Failed: {e}")