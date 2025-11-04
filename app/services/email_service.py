import os
import resend
from flask import current_app

class EmailService:
    def __init__(self):
        self.api_key = current_app.config.get('RESEND_API_KEY')
        self.from_email = current_app.config.get('RESEND_FROM_EMAIL')
        self.app_name = current_app.config.get('APP_NAME')
        self.frontend_url = current_app.config.get('FRONTEND_URL', 'https://agri-smart-detect.onrender.com')
        
        # Configure Resend API key
        if self.api_key:
            resend.api_key = self.api_key
    
    def send_welcome_email(self, user_email, user_name):
        """Send welcome email after registration"""
        subject = f"Welcome to {self.app_name} - Start Your Smart Farming Journey!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #2d5016 0%, #4CAF50 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fff8; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e8f5e8; }}
                .button {{ background: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }}
                .feature {{ margin: 20px 0; padding: 15px; background: white; border-radius: 5px; border-left: 4px solid #4CAF50; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e8f5e8; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌱 Welcome to {self.app_name}!</h1>
                    <p>Smart Farming, Healthy Crops, Better Yields</p>
                </div>
                <div class="content">
                    <h2>Hello {user_name}!</h2>
                    <p>Welcome to Africa's premier AI-powered crop disease detection platform. We're excited to help you protect your harvest and maximize your yields.</p>
                    
                    <div class="feature">
                        <h3>🚀 Get Started Today</h3>
                        <p>Upload photos of your crops to get instant disease analysis and treatment recommendations.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>🔍 AI-Powered Detection</h3>
                        <p>Our advanced machine learning models can identify common African crop diseases with high accuracy.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>💡 Expert Recommendations</h3>
                        <p>Get personalized treatment plans and prevention tips tailored to your specific crops and conditions.</p>
                    </div>
                    
                    <center>
                        <a href="{self.frontend_url}/scan" class="button">Start Scanning Your Crops</a>
                    </center>
                </div>
                <div class="footer">
                    <p>Need help? Contact our support team at support@agri-smart-detect.com</p>
                    <p>&copy; 2024 {self.app_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(user_email, subject, html_content)
    
    def send_disease_report(self, user_email, user_name, report_data):
        """Send disease analysis report to farmer"""
        status_emoji = "✅" if report_data['is_healthy'] else "⚠️"
        status_text = "Healthy" if report_data['is_healthy'] else "Disease Detected"
        status_color = "#2d5016" if report_data['is_healthy'] else "#e65100"
        
        subject = f"Crop Analysis Report: {report_data['crop_name']} - {status_text}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {'#e8f5e8' if report_data['is_healthy'] else '#fff3e0'}; 
                         color: {'#2d5016' if report_data['is_healthy'] else '#e65100'}; 
                         padding: 25px; text-align: center; border-radius: 10px; border: 1px solid {'#4CAF50' if report_data['is_healthy'] else '#ff9800'}; }}
                .content {{ background: #f8f9fa; padding: 25px; border-radius: 10px; margin-top: 20px; }}
                .status {{ font-size: 24px; font-weight: bold; margin: 15px 0; }}
                .info-box {{ background: white; padding: 20px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #4CAF50; }}
                .urgent {{ background: #ffebee; border-left: 4px solid #f44336; }}
                .confidence {{ background: #e3f2fd; padding: 10px; border-radius: 5px; text-align: center; margin: 15px 0; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{status_emoji} {status_text}</h1>
                    <p><strong>Crop:</strong> {report_data['crop_name']} | <strong>Confidence:</strong> {report_data['confidence']}%</p>
                </div>
                
                <div class="content">
                    <h2>Hello {user_name},</h2>
                    <p>Here's the analysis of your recent crop scan:</p>
                    
                    <div class="confidence">
                        <strong>AI Confidence Level: {report_data['confidence']}%</strong>
                    </div>
                    
                    <div class="info-box {'' if report_data['is_healthy'] else 'urgent'}">
                        <h3>{"🛡️ Plant Health Status" if report_data['is_healthy'] else "💊 Disease Identified"}</h3>
                        <p><strong>{report_data['status_message']}</strong></p>
                        {f"<p><strong>Disease:</strong> {report_data['disease_name']}</p>" if not report_data['is_healthy'] else ""}
                    </div>
                    
                    <div class="info-box">
                        <h3>{"🌱 Maintenance Recommendations" if report_data['is_healthy'] else "🩺 Recommended Treatment"}</h3>
                        <p>{report_data['treatment']}</p>
                    </div>
                    
                    {f'''
                    <div class="info-box">
                        <h3>📝 Prevention Tips</h3>
                        <p>{report_data['prevention']}</p>
                    </div>
                    ''' if report_data.get('prevention') else ''}
                    
                    <center>
                        <a href="{self.frontend_url}/reports" class="button" style="background: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            View Full Report
                        </a>
                    </center>
                </div>
                
                <div class="footer">
                    <p>This is an automated report from {self.app_name}'s AI analysis system.</p>
                    <p>&copy; 2024 {self.app_name}. Protecting your harvest.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(user_email, subject, html_content)
    
    def send_password_reset(self, user_email, reset_token):
        """Send password reset email"""
        subject = "Reset Your Agri Smart Detect Password"
        
        reset_url = f"{self.frontend_url}/reset-password?token={reset_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #2d5016 0%, #4CAF50 100%); color: white; padding: 25px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fff8; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e8f5e8; }}
                .button {{ background: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .warning {{ background: #fff3e0; padding: 15px; border-radius: 5px; border-left: 4px solid #ff9800; margin: 15px 0; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e8f5e8; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                    <p>{self.app_name} Account Security</p>
                </div>
                <div class="content">
                    <h2>Hello,</h2>
                    <p>You requested to reset your password for your {self.app_name} account.</p>
                    <p>Click the button below to create a new password:</p>
                    
                    <center>
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </center>
                    
                    <div class="warning">
                        <p><strong>⚠️ Important:</strong> This link will expire in 1 hour for security reasons.</p>
                        <p>If you didn't request this password reset, please ignore this email and ensure your account is secure.</p>
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">
                        Can't click the button? Copy and paste this link in your browser:<br>
                        <code style="background: #f5f5f5; padding: 5px; border-radius: 3px;">{reset_url}</code>
                    </p>
                </div>
                <div class="footer">
                    <p>This is an automated security message from {self.app_name}.</p>
                    <p>&copy; 2024 {self.app_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(user_email, subject, html_content)
    
    def _send_email(self, to_email, subject, html_content):
        """Send email using Resend"""
        try:
            if not self.api_key:
                print(f"Resend not configured. Would send email to {to_email}: {subject}")
                return True  # Return success in development
            
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
            
            response = resend.Emails.send(params)
            
            print(f"Email sent to {to_email}. Response: {response}")
            return True
            
        except Exception as e:
            print(f"Failed to send email to {to_email}: {str(e)}")
            return False