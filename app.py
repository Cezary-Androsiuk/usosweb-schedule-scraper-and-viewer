from flask import Flask, render_template, request, redirect, url_for, session, Response

# from old_uwb_connector import asyncio, update_cookies, download_schedule_image, schedule_image_name
from uwb_connector import download_schedule_safe
from date_validator import todays_week, to_week_date, week_range, week_forward, week_backwards

app = Flask(__name__)
app.secret_key = "secret_key_xd"

@app.route('/')
def home():
    
    schedule_date = request.args.get('schedule_date')
    if not schedule_date:
        current_week = todays_week();
        return redirect(url_for('home', schedule_date=current_week))
    else:
        current_week = to_week_date(schedule_date);
    
    
    next_week = week_forward(current_week)
    previous_week = week_backwards(current_week)
    current_week_range = week_range(current_week)
    
    return render_template(
        'schedule.html', 
        previous_week=previous_week,
        current_week=current_week, 
        current_week_range=current_week_range,
        next_week=next_week)
    

@app.route('/stream-data/<schedule_date>')
def stream_data(schedule_date):
    return Response(download_schedule_safe(schedule_date), mimetype='text/event-stream')



@app.route('/error')
def error():
    return render_template(
        'error.html',
        error_info=request.args.get('error_info', 'No error now')
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)