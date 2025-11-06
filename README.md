# USOSweb Schedule Scraper and Viewer

## About This Project
This program starts a Flask server that allows any user on your local network to view your weekly class schedule.

On every connection from a local device, the app logs into your USOSweb account in real-time and scrapes the latest schedule. The application also allows the end-user to select a specific week they want to view.

### Note
The end user is presented with only a static image scraped from the USOSweb page.

## Configuration & Setup
To run the program, you must set the following two environment variables on the server:

```UWB_LOGIN``` - The email for your USOSweb account

```UWB_PASSWORD``` - The password for your USOSweb account

## Images

### Loading status
![Loading status](https://github.com/Cezary-Androsiuk/uwb-schedule-scraper-and-viewer/blob/master/screenshots/loading_status.png "Loading status") 

### Loaded schedule
![Loaded schedule](https://github.com/Cezary-Androsiuk/uwb-schedule-scraper-and-viewer/blob/master/screenshots/loaded_schedule.png "Loaded schedule") 

### Error while loading
![Error while loading](https://github.com/Cezary-Androsiuk/uwb-schedule-scraper-and-viewer/blob/master/screenshots/loading_error.png "Error while loading") 

### Error with invalid url
![Error with invalid url](https://github.com/Cezary-Androsiuk/uwb-schedule-scraper-and-viewer/blob/master/screenshots/error_with_invalid_url.png "Error with invalid url") 