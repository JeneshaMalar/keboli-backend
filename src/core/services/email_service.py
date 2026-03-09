import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from src.config.settings import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

    async def send_invitation_email(self, candidate_email: str, candidate_name: str, assessment_title: str, token: str):
        invite_url = f"{settings.FRONTEND_URL}/interview?token={token}"
        
        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=candidate_email,
            subject=f"Invitation: Interview for {assessment_title}",

            html_content = f"""
            <div style="background-color:#f3f4f6;padding:40px 0;font-family:Arial,Helvetica,sans-serif;">
            <table align="center" width="600" cellpadding="0" cellspacing="0" style="background:white;border-radius:10px;overflow:hidden;box-shadow:0 4px 10px rgba(0,0,0,0.08);">

                <!-- Header -->
                <tr>
                <td style="background:#2563eb;padding:20px;text-align:center;color:white;font-size:22px;font-weight:bold;">
                    AI Interview Platform
                </td>
                </tr>

                <!-- Body -->
                <tr>
                <td style="padding:30px;color:#333;">
                    <h2 style="margin-top:0;">Hello {candidate_name},</h2>

                    <p style="font-size:16px;line-height:1.6;">
                    You have been invited to participate in an 
                    <strong>AI-powered interview</strong> for the assessment:
                    </p>

                    <p style="font-size:18px;font-weight:bold;color:#2563eb;">
                    {assessment_title}
                    </p>

                    <p style="font-size:16px;line-height:1.6;">
                    Click the button below to begin your interview session.
                    </p>

                    <!-- Button -->
                    <div style="text-align:center;margin:30px 0;">
                    <a href="{invite_url}"
                        style="background:#2563eb;color:white;padding:14px 28px;text-decoration:none;border-radius:6px;font-size:16px;font-weight:bold;display:inline-block;">
                        Start Interview
                    </a>
                    </div>

                    <!-- Important Warning -->
                    <div style="background:#fff4e5;border-left:4px solid #f59e0b;padding:15px;margin:25px 0;font-size:14px;color:#92400e;">
                    <strong>Important:</strong><br>
                    This interview link is <strong>single-use only</strong>. Once you click and start the interview,
                    the link cannot be accessed again. Please ensure you have a stable internet connection
                    and a quiet environment before starting.
                    </div>

                    <!-- Fallback link -->
                    <p style="font-size:14px;color:#666;">
                    If the button doesn't work, copy and paste the link below into your browser:
                    </p>

                    <p style="font-size:14px;color:#2563eb;word-break:break-all;">
                    {invite_url}
                    </p>

                    <p style="font-size:14px;color:#666;margin-top:20px;">
                    This invitation link will expire soon. Please complete your interview before it expires.
                    </p>
                </td>
                </tr>

                <!-- Footer -->
                <tr>
                <td style="background:#f9fafb;padding:20px;text-align:center;font-size:12px;color:#777;">
                    © {datetime.now().year} AI Interview Platform <br>
                    This is an automated message. Please do not reply.
                </td>
                </tr>

            </table>
            </div>
            """
        )
        try:
            response = self.sg.send(message)
            return response.status_code
        except Exception as e:
            logger.error(f"Error sending email via SendGrid: {e}")
            return None
