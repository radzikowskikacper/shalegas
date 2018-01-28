[ENGLISH VERSION]

1. The system was tested on Ubuntu 16.04.

2. Install required packages
  $ sudo apt-get install python2.7 postgresql postgresql-server-dev-all lighttpd python-pip python2.7-dev libjpeg-dev

3. Install deb package.
  $ sudo dpkg -i sweetspot.deb

4. After installation, it is necessary to create a PostgreSQL database and user according to commands below:
  $ sudo -u postgres createuser --no-superuser --createdb --no-createrole sweetspot
  $ sudo -u postgres createdb -O sweetspot sweetspot
  $ sudo -u postgres psql -c "alter user sweetspot with encrypted password 'sweetspot';"

5. In case when entire machine may be used by the system, follow steps below
  a) Install python packages
    $ sudo pip install Django==1.6.2 Pillow==2.4.0 gunicorn==18.0 psycopg2==2.5.2

  b) Initialze database:
    i) from data files
      $ sudo -s
      # cd /srv/sweetspot/
      # export SWEETSPOT_LOG_DIR=/var/log
      # python app/manage.py syncdb --noinput
      # python app/manage.py loaddata app/meanings/fixtures/*.json app/users/fixtures/sweetspot.json

    ii) from json file
      $ sudo -s
      # cd /srv/sweetspot/
      # export SWEETSPOT_LOG_DIR=/var/log
      # python app/manage.py syncdb --noinput
      # python app/manage.py loaddata plik.json

    iii) using PostgreSQL dump
      sudo su postgres -c 'pg_restore -d sweetspot -Fc plik.db'

  c) Go to step 7.

6. In case of installation inside virtual environment, follow steps below
  a) Install virtualenv
    $ sudo pip install virtualenv

  b) Install required packages
    $ cd /srv/sweetspot
    $ sudo virtualenv venv
    $ source venv/bin/activate
    (venv)$ sudo venv/bin/pip install Django==1.6.2 Pillow==2.4.0 gunicorn==18.0 psycopg2==2.5.2
    (venv)$ deactivate

  c) Initialize database:
    i) from data files
      $ sudo -s
      # cd /srv/sweetspot/
      # source venv/bin/activate
      (venv)# export SWEETSPOT_LOG_DIR=/var/log
      (venv)# python app/manage.py syncdb --noinput
      (venv)# python app/manage.py loaddata app/meanings/fixtures/*.json app/users/fixtures/sweetspot.json
      (venv)# deactivate # deaktywuje virtualenv

    ii) from json file
      $ sudo -s
      # cd /srv/sweetspot/
      # source venv/bin/activate
      (venv)# export SWEETSPOT_LOG_DIR=/var/log
      (venv)# python app/manage.py syncdb --noinput
      (venv)# python app/manage.py loaddata plik.json
      (venv)# deactivate # deaktywuje virtualenv

    iii) from PostgreSQL dump
      sudo su postgres -c 'pg_restore -d sweetspot -Fc plik.db'

7. Restart lighttpd
  $ sudo service lighttpd reload
  $ sudo service lighttpd restart

8. Add server IP in /srv/sweetspot/app/settings.py in ALLOWED_HOSTS section
   
9. Start system
  $ sudo service sweetspot start

10. Aplikacja powinna być dostępna pod adresem 'http://localhost'
