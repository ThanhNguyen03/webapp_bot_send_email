from flask import Flask, render_template, request, redirect, url_for, jsonify
import csv
import os 
import tkinter as tk
from tkinter import filedialog
import smtplib
import ssl
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
#import gspread
import email.utils as eut
from oauth2client.service_account import ServiceAccountCredentials
import time
import os
from crontab import CronTab
import csv 
import schedule
import threading

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('abc.html')  # Trả về trang chủ của ứng dụng web

@app.route('/save', methods=['POST'])
def save_data():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        sheet_link = request.form['sheet_link']
        file = request.form['file']
        timeloop = request.form['timeloop']

        # Lưu các giá trị vào file csv
        with open("input.csv", "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["email", "password", "sheet_link", "file", "timeloop"])
            writer.writerow([email, password, sheet_link, file, timeloop])

    return redirect(url_for('index'))  # Chuyển hướng người dùng về trang chủ sau khi lưu dữ liệu

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        uploaded_file = request.files['file_input']
        if uploaded_file:
            # Lấy tên tệp
            filename = uploaded_file.filename
            # Lưu tệp vào thư mục uploads (hoặc bất kỳ thư mục nào bạn muốn)
            uploaded_file.save(f'uploads/{filename}')
            return f'Tệp "{filename}" đã được tải lên thành công.'
    
    return 'Lỗi khi tải lên tệp.'

@app.route('/show_status', methods=['POST'])
def show_status():
    message = "Đang gửi email đến {}"
    color = "green"  # Màu sắc bạn muốn sử dụng
    return jsonify(message=message, color=color)

@app.route('/send', methods=['POST'])
def send_data():
   if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        sheet_link = request.form['sheet_link']
        interval = request.form['interval'] if 'interval' in request.form else 0

        # Xử lý tệp đã tải lên
        uploaded_files = request.files.getlist("file")
        file_paths = []
        for file in uploaded_files:
            file_path = os.path.join("uploads", file.filename)
            file.save(file_path)
            file_paths.append(file_path)

        # Thực hiện xử lý gửi email tại đây (đoạn mã gửi email của bạn)
        global count # Biến đếm số lần gửi email
        if count < 200: # Kiểm tra nếu chưa đủ 200 lần
            with open("input.csv", "r") as f: # Mở file .csv chứa các thông số
                reader = csv.DictReader(f) # Tạo một đối tượng DictReader để đọc file
                for row in reader: # Duyệt qua từng dòng trong file
                    email = row["email"] # Lấy giá trị của cột email
                    password = row["password"] # Lấy giá trị của cột password
                    sheet_link = row["sheet_link"] # Lấy giá trị của cột sheet_link
                    file_paths = row["file"] # Lấy giá trị của cột file

            smtp_server = 'smtp.gmail.com'
            smtp_port = 587
        
            output_df = pd.DataFrame(columns=['name', 'email', 'sent time'])
            # fetch data from Google Sheet
            try:
                sheet_id = sheet_link.split('/')[5]
                url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx'
                print(f"url: {url}")
                df = pd.read_excel(url)
            except Exception as e:
                print(e)
                return
            for index, row in df.iterrows():
                if '@' in str(row['Email']) and '.' in str(row['Email']).split('@')[1]:
                    email_to = [row['Email']]
                    email_subject = row['Subject']
                    email_message = row['Message'].replace('@name', row['Name'])

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
                            count +=1 
                        except Exception as e:
                            print("Error:", str(e))
                            df.at[index, 'Status'] = 'Failed'
                            
                        time.sleep(interval)
                else:
                    df.at[index, 'Status'] = 'Failed'
                    output_df = output_df.append({'name': row['Name'], 'email': 'null', 'sent time': 'null'}, ignore_index=True)
            output_df.to_excel('output.xlsx', sheet_name='Sheet1', index=False)
            status_message = "Email đã được gửi thành công"
    
            return render_template('index.html', status_message=status_message)
            
        return "Invalid request method."
@app.route('/start_schedule', methods=['POST'])
def start_schedule():
    global timeloop_schedule

    if request.method == 'POST':
        timeloop = request.form.get('timeloop')
        
        if timeloop_schedule is not None:
            timeloop_schedule.cancel()

        timeloop_schedule = schedule.every().day.at(timeloop).do(send_data)
        return "Schedule started."

@app.route('/stop_schedule', methods=['POST'])
def stop_schedule():
    global timeloop_schedule

    if timeloop_schedule is not None:
        timeloop_schedule.cancel()
        return "Schedule stopped."
    else:
        return "No active schedule."

if __name__ == '__main__':
    app.run(debug=True)