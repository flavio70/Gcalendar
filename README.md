# Gcalendar
Google calendar API Example driving Raspberry GPIOs


- Download required packages

        sudo apt-get install git rpi.gpio python3-httplib2
        sudo pip3 install PySocks
        sudo pip3 install apsscheduler
        sudo pip3 install --upgrade google-api-python-client

- Get the main code

        git clone https://github.com/flavio70/Gcalendar.git

- Create the folder /srv/gcalendar

        sudo mkdir -p /srv/gcalendar

- Copy the main code folder daemon

        sudo cp -R Gcalendar/daemon /srv/gcalendar
        
 
 
- Give the rights

        sudo chown -R root:root /srv/gcalendar
        sudo chmod -R 775 /srv/gcalendar
 
  
  into /srv/gcalendar/daemon/gcalendar.py source code the CAL_ID variable must be set to the correct google calendar ID.
  Please see https://developers.google.com/google-apps/calendar/ for help on setting google api rights.
  
- Get the OAuth2 credential file for your calendar
        
        get the json credential files from https://console.developers.google.com
        copy the file into /srv/gcalendar/daemon/client_secret.json
  see https://developers.google.com/google-apps/calendar/ for help on how to generate credentials for your application.


- Create the log files with correct rights

        sudo mkdir /var/log/gcalendar
        sudo touch /var/log/gcalendar/status.log
        sudo touch /var/log/gcalendar/error.log
        sudo chown -R root:root /var/log/gcalendar
        sudo chmod -R 775 /var/log/gcalendar

- Copy the logrotate file with correct rights

        sudo cp Gcalendar/install/logrotate.erb /etc/logrotate.d/gcalendar
        sudo chmod 755 /etc/logrotate.d/gcalendar
        sudo chown root:root /etc/logrotate.d/gcalendar

- Copy init.d files in /etc/init.d with correct rights

        sudo cp Gcalendar/install/init.d.erb /etc/init.d/gcalendar
        sudo chmod 755 /etc/init.d/gcalendar
        sudo chown root:root /etc/init.d/gcalendar


- Enable the service

        sudo systemctl enable gcalendar


- Start the service

        sudo service gcalendar start

