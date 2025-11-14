from flask import Flask, render_template, request, redirect, url_for, session, Response
import json
from pathlib import Path
from datetime import datetime, timedelta

# from old_uwb_connector import asyncio, update_cookies, download_schedule_image, schedule_image_name
from uwb_connector import download_schedule_safe, schedule_image_name
from date_validator import todays_week, to_week_date, week_range, week_forward, week_backwards

app = Flask(__name__)
app.secret_key = "secret_key_xd"

@app.route('/')
def root():
    
    # read "GET" variable
    schedule_date = request.args.get('schedule_date')
    current_week = None
    todays_week_str = todays_week()
    try:

        if not schedule_date:
            # if is None, then use todays week
            current_week = todays_week_str
            return redirect(url_for('root', schedule_date=current_week))
        else:
            # if date is specified, then use it, but first parse it
            current_week = to_week_date(schedule_date);
    
    except Exception as e:
        return redirect(url_for('error', error_info=e))
    
    # create values for the page
    previous_week = week_backwards(current_week)
    next_week = week_forward(current_week)
    current_week_range = week_range(current_week)
    todays_week_range = week_range(todays_week_str)
    
    return render_template(
        'schedule.html', 
        previous_week=previous_week,
        current_week=current_week, 
        current_week_range=current_week_range,
        todays_week_range=todays_week_range,
        next_week=next_week)
    

def is_file_new_enough(image_name, seconds=10*60):
    file_path = Path(image_name)

    now = datetime.now()
    max_age_delta = timedelta(seconds=seconds)
    cutoff_time = now - max_age_delta

    if file_path.is_file():
        file_mod_timestamp = file_path.stat().st_mtime
        file_mod_time = datetime.fromtimestamp(file_mod_timestamp)
        if file_mod_time >= cutoff_time:
            return True
        else:
            return False
    else:
        return False # if not exist also return false


@app.route('/stream-data/<schedule_date>')
def stream_data(schedule_date):
    # check if image existing image is not older than 10min, if so, it can be used

    image_name = schedule_image_name(schedule_date)

    if is_file_new_enough(image_name=image_name, seconds=10*60):
        def exisiting_image_stream(image_name):
            message = {'type': 'link', 'payload': f'{image_name}'}
            yield f'data: {json.dumps(message)}\n\n'
        
        return Response(exisiting_image_stream(image_name=image_name), mimetype='text/event-stream')
    


    return Response(download_schedule_safe(schedule_date), mimetype='text/event-stream')



@app.route('/error')
def error():
    return render_template(
        'error.html',
        error_info=request.args.get('error_info', 'No error now')
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, threaded=True)