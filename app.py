from flask import Flask, render_template, request, redirect, url_for, session
from datetime import date
import uuid
import os

from uwb_connector import asyncio, update_cookies, download_schedule_image, schedule_image_name
from date_validator import todays_week, week_range, week_forward, week_backwards

app = Flask(__name__)
app.secret_key = "secret_key_xd"

@app.route('/')
def home():
    
    schedule_date = request.args.get('schedule_date')
    if not schedule_date:
        # first time oppened => update cookies
        # asyncio.run(update_cookies())

        current_week = todays_week();
    else:
        current_week = schedule_date;
    
    
    next_week = week_forward(current_week)
    previous_week = week_backwards(current_week)
    current_week_range = week_range(current_week)

    try:
        print("week:", current_week)
        asyncio.run(download_schedule_image(current_week))
    except Exception as e:
        print(f'downloading image failed: {e}')
        return redirect(url_for('error', error_info=e))

    image_path = schedule_image_name(current_week)
    
    return render_template(
        'index.html', 
        previous_week=previous_week,
        current_week=current_week, 
        current_week_range=current_week_range,
        next_week=next_week,
        image_path=image_path)


@app.route('/error')
def error():
    return render_template(
        'error.html',
        error_info=request.args.get('error_info', 'No error now')
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)