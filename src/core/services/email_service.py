"""Email service for sending transactional emails via SendGrid."""

import logging
from datetime import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from src.config.settings import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional emails via the SendGrid API.

    Handles invitation emails to candidates and completion
    notifications to hiring managers.
    """

    def __init__(self) -> None:
        self.sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

    async def send_invitation_email(
        self,
        candidate_email: str,
        candidate_name: str,
        assessment_title: str,
        token: str,
    ) -> int | None:
        """Send an interview invitation email to a candidate.

        Args:
            candidate_email: Recipient email address.
            candidate_name: Candidate's display name for personalization.
            assessment_title: Title of the assessment being invited to.
            token: Secure invitation token for the interview URL.

        Returns:
            The SendGrid HTTP status code on success, or None on failure.
        """
        invite_url = f"{settings.FRONTEND_URL}/interview?token={token}"

        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=candidate_email,
            subject=f"Invitation: Interview for {assessment_title}",
            html_content=f"""
            <div style="background-color:#f3f4f6;padding:40px 0;font-family:Arial,Helvetica,sans-serif;">
            <table align="center" width="600" cellpadding="0" cellspacing="0" style="background:white;border-radius:10px;overflow:hidden;box-shadow:0 4px 10px rgba(0,0,0,0.08);">

                <!-- Header -->
                <tr>
                <td style="background:#2563eb;padding:20px;text-align:center;color:white;font-size:22px;font-weight:bold;">
                   Keboli
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
                    &copy; {datetime.now().year} AI Interview Platform <br>
                    This is an automated message. Please do not reply.
                </td>
                </tr>

            </table>
            </div>
            """,
        )
        try:
            response = self.sg.send(message)
            return response.status_code
        except Exception as e:
            logger.error(f"Error sending email via SendGrid: {e}")
            return None

    async def send_interview_completion_email(
        self,
        manager_email: str,
        candidate_name: str,
        assessment_title: str,
        session_id: str,
    ) -> int | None:
        """Send an interview completion notification to a hiring manager.

        Args:
            manager_email: Recipient hiring manager email.
            candidate_name: Name of the candidate who completed the interview.
            assessment_title: Title of the completed assessment.
            session_id: Session UUID for the evaluation report link.

        Returns:
            The SendGrid HTTP status code on success, or None on failure.
        """
        report_url = f"{settings.FRONTEND_URL}/evaluation/{session_id}"
        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=manager_email,
            subject=f"Interview Completed: {candidate_name} for {assessment_title}",
            html_content=f"""
           <div style="background-color:#f3f6fb;padding:50px 0;font-family:Arial,Helvetica,sans-serif;">
  <table align="center" width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 6px 18px rgba(0,0,0,0.08);">

    <!-- Header -->
    <tr>
      <td style="background:linear-gradient(90deg,#2563eb,#1e40af);padding:22px;text-align:center;color:#ffffff;font-size:24px;font-weight:700;letter-spacing:1px;">
        Keboli
      </td>
    </tr>

    <!-- Body -->
    <tr>
      <td style="padding:35px 40px;color:#374151;">

        <h2 style="margin-top:0;font-size:22px;color:#111827;">Interview Completed 🎉</h2>

        <p style="font-size:16px;line-height:1.7;margin:18px 0;">
          Great news! <strong>{candidate_name}</strong> has successfully completed their
          AI-powered interview for the <strong>{assessment_title}</strong> assessment.
        </p>

        <p style="font-size:16px;line-height:1.7;margin:18px 0;">
          You can now review the candidate's performance, including their detailed
          evaluation results and full interview transcript.
        </p>

        <!-- Button -->
        <div style="text-align:center;margin:35px 0;">
          <a href="{report_url}"
             style="background:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:8px;font-size:16px;font-weight:600;display:inline-block;box-shadow:0 4px 10px rgba(37,99,235,0.35);">
            View Evaluation Report
          </a>
        </div>

        <p style="font-size:14px;color:#6b7280;line-height:1.6;margin-top:25px;">
          If the button above does not work, copy and paste the following link into your browser:
        </p>

        <p style="font-size:14px;color:#2563eb;word-break:break-all;">
          {report_url}
        </p>

      </td>
    </tr>

    <!-- Divider -->
    <tr>
      <td style="border-top:1px solid #e5e7eb;"></td>
    </tr>

    <!-- Footer -->
    <tr>
      <td style="padding:20px 40px;text-align:center;font-size:13px;color:#9ca3af;">
        &copy; 2026 Keboli. All rights reserved.
      </td>
    </tr>

  </table>
</div>
            """,
        )
        try:
            response = self.sg.send(message)
            return response.status_code
        except Exception as e:
            logger.error(f"Error sending email via SendGrid: {e}")
            return None
