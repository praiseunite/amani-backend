"""
HTML email templates for Amani Escrow.
Responsive design with inline CSS for email compatibility.
"""


def get_verification_email_html(name: str, otp: str) -> str:
    """
    Generate HTML email for account verification.

    Args:
        name: User's full name
        otp: 6-digit verification code

    Returns:
        HTML email content
    """
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Account - Amani Escrow</title>
    <style>
        @media only screen and (max-width: 600px) {{
            .container {{ width: 100% !important; }}
            .otp-code {{ font-size: 20px !important; padding: 12px 20px !important; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; color: #333;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8f9fa;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table class="container" width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 700; letter-spacing: -1px;">Amani Escrow</h1>
                            <p style="margin: 8px 0 0 0; color: #e8eaf6; font-size: 16px; font-weight: 300;">Secure Transactions Made Simple</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 50px 40px;">
                            <h2 style="margin: 0 0 20px 0; color: #2d3748; font-size: 24px; font-weight: 600;">Verify Your Account</h2>
                            
                            <p style="margin: 0 0 30px 0; color: #4a5568; font-size: 16px; line-height: 1.6;">
                                Hi {name},<br><br>
                                Welcome to Amani Escrow! To complete your registration and start securing your transactions, please verify your email address using the code below:
                            </p>
                            
                            <!-- OTP Code -->
                            <div style="text-align: center; margin: 40px 0;">
                                <div class="otp-code" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 20px 40px; border-radius: 8px; font-size: 28px; font-weight: 700; letter-spacing: 8px; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
                                    {otp}
                                </div>
                            </div>
                            
                            <p style="margin: 30px 0 20px 0; color: #4a5568; font-size: 16px; line-height: 1.6;">
                                <strong>Important:</strong> This verification code will expire in <span style="color: #e53e3e;">10 minutes</span>. 
                                If you didn't create an account with Amani Escrow, please ignore this email.
                            </p>
                            
                            <div style="background-color: #f7fafc; border-left: 4px solid #667eea; padding: 20px; margin: 30px 0; border-radius: 4px;">
                                <p style="margin: 0; color: #2d3748; font-size: 14px; line-height: 1.5;">
                                    <strong>Security Tip:</strong> Never share your verification code with anyone. Our team will never ask for your code.
                                </p>
                            </div>
                            
                            <p style="margin: 30px 0 0 0; color: #4a5568; font-size: 16px;">
                                Best regards,<br>
                                <strong>The Amani Escrow Team</strong>
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f7fafc; padding: 30px 40px; text-align: center; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 15px 0; color: #718096; font-size: 14px;">
                                © 2025 Amani Escrow. All rights reserved.
                            </p>
                            <p style="margin: 0; color: #a0aec0; font-size: 12px;">
                                This email was sent to you because you signed up for an Amani Escrow account.<br>
                                If you have any questions, contact us at <a href="mailto:support@amani.com" style="color: #667eea;">support@amani.com</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def get_welcome_email_html(name: str) -> str:
    """
    Generate HTML welcome email for verified users.

    Args:
        name: User's full name

    Returns:
        HTML email content
    """
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Amani Escrow</title>
    <style>
        @media only screen and (max-width: 600px) {{
            .container {{ width: 100% !important; }}
            .button {{ display: block !important; width: 100% !important; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; color: #333;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8f9fa;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table class="container" width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 700; letter-spacing: -1px;">Welcome to Amani Escrow</h1>
                            <p style="margin: 8px 0 0 0; color: #e8eaf6; font-size: 16px; font-weight: 300;">Your Account is Now Active</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 50px 40px;">
                            <h2 style="margin: 0 0 20px 0; color: #2d3748; font-size: 24px; font-weight: 600;">Congratulations, {name}!</h2>
                            
                            <p style="margin: 0 0 30px 0; color: #4a5568; font-size: 16px; line-height: 1.6;">
                                Your email has been successfully verified and your Amani Escrow account is now active. 
                                You can now start creating secure escrow transactions with confidence.
                            </p>
                            
                            <!-- Features -->
                            <div style="background-color: #f7fafc; border-radius: 8px; padding: 30px; margin: 30px 0;">
                                <h3 style="margin: 0 0 20px 0; color: #2d3748; font-size: 18px;">What you can do now:</h3>
                                <ul style="margin: 0; padding-left: 20px; color: #4a5568; line-height: 1.8;">
                                    <li>Create and manage escrow transactions</li>
                                    <li>Connect with verified freelancers and clients</li>
                                    <li>Track transaction progress in real-time</li>
                                    <li>Access secure payment processing</li>
                                    <li>Complete KYC verification for enhanced security</li>
                                </ul>
                            </div>
                            
                            <!-- CTA Button -->
                            <div style="text-align: center; margin: 40px 0;">
                                <a href="#" class="button" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
                                    Start Your First Transaction
                                </a>
                            </div>
                            
                            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 30px 0;">
                                <p style="margin: 0; color: #856404; font-size: 14px; line-height: 1.5;">
                                    <strong>Security Reminder:</strong> Always verify transaction details before releasing funds. 
                                    Our platform provides additional security layers, but staying vigilant is key to successful transactions.
                                </p>
                            </div>
                            
                            <p style="margin: 30px 0 0 0; color: #4a5568; font-size: 16px;">
                                If you have any questions, our support team is here to help.<br><br>
                                Best regards,<br>
                                <strong>The Amani Escrow Team</strong>
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f7fafc; padding: 30px 40px; text-align: center; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 15px 0; color: #718096; font-size: 14px;">
                                © 2025 Amani Escrow. All rights reserved.
                            </p>
                            <p style="margin: 0; color: #a0aec0; font-size: 12px;">
                                Need help? Contact us at <a href="mailto:support@amani.com" style="color: #667eea;">support@amani.com</a><br>
                                Visit our website at <a href="https://amani.com" style="color: #667eea;">amani.com</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
