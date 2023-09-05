import tkinter as tk
from tkinter import filedialog
import smtplib
import ssl
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import gspread
import email.utils as eut
from oauth2client.service_account import ServiceAccountCredentials
import time
import os

def select_files():
    file_paths = filedialog.askopenfilenames(filetypes=(("All files", "*"),))
    file_entry.delete(0, tk.END)
    file_entry.insert(0, ', '.join(file_paths))

def send_data():
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    email = email_entry.get()
    password = password_entry.get()
    sheet_link = sheet_link_entry.get()
    file_paths = file_entry.get()
    output_df = pd.DataFrame(columns=['name', 'email', 'sent time'])
    # fetch data from Google Sheet
    try:
        sheet_id = sheet_link.split('/')[5]
        url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx'
        print(f"url: {url}")
        df = pd.read_excel(url)
    except Exception as e:
        print(e)
        status_label.config(text="Invalid Google Sheet link", fg="red")
        return
    interval = int(interval_entry.get()) if interval_entry.get() else 0
    notification = tk.StringVar()
    notification_label = tk.Label(root, textvariable=notification)
    notification_label.pack()
    for index, row in df.iterrows():
        if '@' in str(row['Email']) and '.' in str(row['Email']).split('@')[1]:
            email_to = [row['Email']]
            email_subject = row['Subject']
            email_message = row['Message'].replace('@name', row['Name'])

            notification.set("Đang gửi email đến {}".format(email_to))
            root.update()
            notification.set("") 
            notification_label.after(3000, notification_label.pack_forget)

            # Format email message with appropriate line breaks
            lines = email_message.split('\n')
            formatted_lines = []
            for line in lines:
                if line.endswith(':'):
                    formatted_lines.append(line + '\n')
                else:
                    formatted_lines.append(line)
            email_message = '<br>'.join(formatted_lines)
            signature = row['Signature']
            email_message += "<br>" + signature

            for recipient in email_to:
                # Create email content
                msg = MIMEMultipart()
                if file_paths:
                    for file_path in file_paths.split(', '):
                        with open(file_path, 'rb') as f:
                            attachment = MIMEApplication(f.read(), _subtype='octet-stream')
                            attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
                            msg.attach(attachment)
                msg.attach(MIMEText(email_message, 'html'))
                # else:
                #     msg = MIMEText(email_message, 'html')

                msg['To'] = eut.formataddr((row['Name'], recipient))
                msg['From'] = eut.formataddr(('Henry Universes', email))
                msg['Subject'] = email_subject

                # Send email
                try:
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    server.login(email, password)
                    server.sendmail(email, recipient, msg.as_string())
                    server.quit()
                    df.at[index, 'Status'] = 'Sent'
                    sent_time = time.strftime('%Y-%m-%d %H:%M:%S')
                    #output_df = pd.concat([output_df, pd.DataFrame({'name': row['Name'], 'email': recipient, 'sent time': sent_time}, index=[0])], ignore_index=True)
                    print('Send email to,', recipient)
                    output_df = output_df.append({'name': row['Name'], 'email': recipient, 'sent time': sent_time}, ignore_index=True)
                except Exception as e:
                    print("Error:", str(e))
                    df.at[index, 'Status'] = 'Failed'
                    
                time.sleep(interval)
        else:
            df.at[index, 'Status'] = 'Failed'
            output_df = output_df.append({'name': row['Name'], 'email': 'null', 'sent time': 'null'}, ignore_index=True)
    output_df.to_excel('output.xlsx', sheet_name='Sheet1', index=False)
    print("All emails sent successfully!")
    status_label.config(text="Tất cả email đã được gửi thành công", fg="green")
    status_label.pack()
    status_label.after(10000, lambda: status_label.pack_forget())

root = tk.Tk()
root.title("Auto send email")

# create the main frame
main_frame = tk.Frame(root, padx=10, pady=10)
main_frame.pack()

# create the email frame
email_frame = tk.LabelFrame(main_frame, text="Email")
email_frame.pack(fill="x", padx=10, pady=10)

email_entry = tk.Entry(email_frame, width=40)
email_entry.pack(padx=10, pady=5)

# create the password frame
password_frame = tk.LabelFrame(main_frame, text="Mật khẩu")
password_frame.pack(fill="x", padx=10, pady=10)

password_entry = tk.Entry(password_frame, show="*", width=40)
password_entry.pack(padx=10, pady=5)

# create the sheet link frame
sheet_link_frame = tk.LabelFrame(main_frame, text="Google Sheet Link")
sheet_link_frame.pack(fill="x", padx=10, pady=10)

sheet_link_entry = tk.Entry(sheet_link_frame, width=40)
sheet_link_entry.pack(padx=10, pady=5)

# create the file frame
file_frame = tk.LabelFrame(main_frame, text="File đính kèm")
file_frame.pack(fill="x", padx=10, pady=10)

file_entry = tk.Entry(file_frame, width=40)
file_entry.pack(side="left", padx=10, pady=5)

file_button = tk.Button(file_frame, text="Chọn tệp", command=select_files)
file_button.pack(side="left", padx=10, pady=5)

# create the status label
status_label = tk.Label(main_frame, text="", font=("Arial", 12))
status_label.pack(pady=10)

# create the send button
send_button = tk.Button(main_frame, text="Gửi", command=send_data)
send_button.pack()

interval_frame = tk.LabelFrame(main_frame, text="Thời gian giữa các email (giây)")
interval_frame.pack(fill="x", padx=10, pady=10)

interval_entry = tk.Entry(interval_frame, width=10)
interval_entry.pack(padx=10, pady=5)

root.mainloop()
