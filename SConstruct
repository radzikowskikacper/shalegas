# -*- mode: Python; main SCons script for sweetspot application -*-
import os, platform, subprocess, re, time, ConfigParser, shutil, sys, signal

SWEETSPOT_VER_MAJOR = '1'
SWEETSPOT_VER_MINOR = '00'
SWEETSPOT_VER_COMPILATION = '0'

#odczytuje wersje kompilacji z wersji repozytorium
ver_repository = subprocess.Popen('hg sum', shell=True, stdout=subprocess.PIPE).communicate()[0]
try:
    SWEETSPOT_VER_COMPILATION = re.search('(?<=parent: )\d+', ver_repository).group()
except BaseException:
    pass

config = ConfigParser.ConfigParser()
config.read('build_custom.ini')

#debug
DEBUG_FLAG = config.get('main','DEBUG') in ['TRUE', 'True', 'true', '1']
SWEETSPOT_VER_INSTALL = config.get('main','VER_INSTALL')

#web
WWW_BROWSER_WINDOWS=config.get('web','WWW_BROWSER_WINDOWS')
WWW_BROWSER_LINUX=config.get('web','WWW_BROWSER_LINUX')
WEB_SRV_PREFIX = config.get('web','WEB_SRV_PREFIX')
WEB_SRV_HOST = config.get('web','WEB_SRV_HOST')
WEB_SRV_PORT = config.get('web','WEB_SRV_PORT')
WEB_CLIENT_HOST = config.get('web','WEB_CLIENT_HOST')
WEB_CLIENT_PORT = config.get('web','WEB_CLIENT_PORT')
DEMO_HOST = config.get('web', 'DEMO_HOST')
DEMO_PORT = config.get('web', 'DEMO_PORT')
DEMO_SSH = config.get('web', 'DEMO_SSH')

#database
DB_NAME=config.get('database','DB_NAME')
DB_USER=config.get('database','DB_USER')
DB_PASSWORD=config.get('database','DB_PASSWORD')


Export('SWEETSPOT_VER_MAJOR SWEETSPOT_VER_MINOR SWEETSPOT_VER_COMPILATION SWEETSPOT_VER_INSTALL DEBUG_FLAG')
Export('WWW_BROWSER_WINDOWS WWW_BROWSER_LINUX')
Export('WEB_SRV_PREFIX WEB_SRV_HOST WEB_SRV_PORT WEB_CLIENT_HOST WEB_CLIENT_PORT')
Export('DB_NAME DB_USER DB_PASSWORD')

vars = Variables('custom.py')
vars.Add(EnumVariable('r','Run the application'\
                      ', l: local lighttpd with WSGI via GUnicorn at \'{web_host}:{web_port}\''\
                      ', d: django internal at \'{web_host}:{web_port}\''.format(web_host=WEB_CLIENT_HOST, web_port=WEB_CLIENT_PORT),
                      'no', allowed_values = ('l', 'd', 'no'), map={}, ignorecase=2) )
vars.Add(EnumVariable('t','Run the tests, \'w\' Python web, \'j\' Javascript client, \'i\' integrity, \'d\' Demo', 
                      'no', allowed_values = ('w', 'j', 'i', 'd', 'no'), map={}, ignorecase=2) )
vars.Add(BoolVariable('cov','Set to 1 to run the coverage reports for python server',0) )
vars.Add(BoolVariable('checkver','Set to 1 to check compilers and libraries versions',0) )
vars.Add(BoolVariable('syncdb','Set to 1 to clean application files and recreate tables in database',0) )
vars.Add(EnumVariable('package','Create a .deb package'\
                      ', l: modyfing local virtualenv\'s path and copying it into package'\
                      ', t: creating temporary virtualenv (downloads pip packages every time)', 'no',
                      allowed_values = ('l', 't', 'no')))
vars.Add(BoolVariable('doxygen', 'Set 1 to generate documentation. The file Doxyfile_in is required',0) )

env = Environment(variables=vars)
Export('env')

Help("""
type 'scons' to build the program and libraries. Settings specific for this project are listed below.
"""
     +
     vars.GenerateHelpText(env)
)

def build_package():
    """build package - ask user if necessary"""
    if DEBUG_FLAG:
        ans = raw_input("DEBUG_FLAG = true. Really build package? [Y/n]:")
        if str(ans) != 'n':
            SConscript("deb/SConscript")
    elif DB_NAME != 'sweetspot' or DB_USER != 'sweetspot':
        ans = raw_input("DB_NAME = '" + str(DB_NAME) + "', DB_USER = '" + str(DB_USER) + "' Really build package? [Y/n]:")
        if str(ans) != 'n':
            SConscript("deb/SConscript")
    else:
            SConscript("deb/SConscript")

if env['package'] == 'l':
    VENV_LOC = config.get('venv', 'VENV_PROD_LOC')
    LOG_LOC = config.get('log', 'LOG_PROD_LOC')
    Export('VENV_LOC', 'LOG_LOC')
    build_package()
elif env['package'] == 't':
    LOG_LOC = config.get('log', 'LOG_PROD_LOC')
    Export('LOG_LOC')
    build_package()
elif env['r'] == 'd':
    os.system('{browser} http://{addr}:{port} &'.format(browser=WWW_BROWSER_LINUX, addr=WEB_CLIENT_HOST, port=WEB_CLIENT_PORT))
    os.system('python web/manage.py runserver {addr}:{port}'.format(addr=WEB_CLIENT_HOST, port=WEB_CLIENT_PORT))
elif env['r'] == 'l':
    os.environ['SWEETSPOT_LOG_DIR'] = config.get('log', 'LOG_DEV_LOC')
    os.system('{browser} http://{addr}:{port} &'.format(browser=WWW_BROWSER_LINUX, addr=WEB_CLIENT_HOST, port=WEB_CLIENT_PORT))
    os.system('lighttpd -f client/lighttpd.develop')
    os.system('gunicorn --chdir web --timeout 0 --workers 1 --bind \'{addr}:{port}\' wsgi:application'.format(addr=WEB_SRV_HOST, port=WEB_SRV_PORT))
    os.system('kill `cat client/lighttpd.pid`')
    del os.environ['SWEETSPOT_LOG_DIR']
elif env['t'] == 'w':
    os.environ['SWEETSPOT_LOG_DIR'] = config.get('log', 'LOG_DEV_LOC')
    if(platform.system() == "Linux"):
        os.system("python web/manage.py test reset version current boreholes measurements images users meanings similarities charts data stratigraphy tables log")
    pass
    del os.environ['SWEETSPOT_LOG_DIR']
elif env['t'] == 'j':
    child_process = subprocess.Popen('python client/tests/srv.py ', shell=True, stdout=subprocess.PIPE)
    os.system( WWW_BROWSER_LINUX + ' client/unit_test_out.html --disable-web-security --enable-file-cookies')
    os.system("kill " + str(child_process.pid))
elif env['t'] == 'i':    
    os.environ['SWEETSPOT_LOG_DIR'] = config.get('log', 'LOG_DEV_LOC')
    django_pid_file = os.path.abspath('django.pid')
    os.system('lighttpd -f client/lighttpd.develop')
    #os.system('python web/manage.py runfcgi daemonize=true host={srv_addr} port={srv_port} pidfile={pid_file}'.format(srv_addr=WEB_SRV_HOST, srv_port=WEB_SRV_PORT, pid_file=django_pid_file))
    os.system('gunicorn --timeout 0 --chdir web --bind \'{addr}:{port}\' wsgi:application &'.format(addr=WEB_SRV_HOST, port=WEB_SRV_PORT))
    os.system('python utils/integr_tests.py {browser} {addr} {port} {dbuser} {dbname} {dbpassword}'.format(browser='chrome', addr=WEB_CLIENT_HOST, port=WEB_CLIENT_PORT, dbuser=DB_USER, dbname=DB_NAME, dbpassword=DB_PASSWORD))
    os.system('python utils/integr_tests.py {browser} {addr} {port} {dbuser} {dbname} {dbpassword}'.format(browser='firefox', addr=WEB_CLIENT_HOST, port=WEB_CLIENT_PORT, dbuser=DB_USER, dbname=DB_NAME, dbpassword=DB_PASSWORD))
    os.system('kill `cat client/lighttpd.pid`')
    os.system('kill `cat django.pid`')
    os.system('killall gunicorn')
    del os.environ['SWEETSPOT_LOG_DIR']
elif env['t'] == 'd':
    os.system('python utils/integr_tests.py {browser} {addr} {port} {dbuser} {dbname} {dbpassword} {ssh_port}'.format(browser='chrome', addr=DEMO_HOST, port=DEMO_PORT, dbuser=DB_USER, dbname=DB_NAME, dbpassword=DB_PASSWORD, ssh_port = DEMO_SSH))
    os.system('python utils/integr_tests.py {browser} {addr} {port} {dbuser} {dbname} {dbpassword} {ssh_port}'.format(browser='firefox', addr=DEMO_HOST, port=DEMO_PORT, dbuser=DB_USER, dbname=DB_NAME, dbpassword=DB_PASSWORD, ssh_port = DEMO_SSH))
elif env['cov'] == 1:
    os.environ['SWEETSPOT_LOG_DIR'] = config.get('log', 'LOG_DEV_LOC')
    if(platform.system() == "Linux"):
        os.system("coverage run --source web/ web/manage.py test reset version current boreholes measurements images users meanings similarities charts data stratigraphy tables log")
        print "\n"
        os.system("coverage report -m")
        print "\n"
    del os.environ['SWEETSPOT_LOG_DIR']

elif env['checkver'] == 1:
    os.system('python utils/checkver.py -d --pip=pip_dev.requirements --bower-dir=client')
elif env['syncdb'] == 1:
    if(platform.system() == "Linux"):
        os.environ['SWEETSPOT_LOG_DIR'] = config.get('log', 'LOG_DEV_LOC')
        os.system('python web/manage.py syncdb --noinput')
        os.system('python web/manage.py loaddata web/meanings/fixtures/*.json web/users/fixtures/sweetspot.json')
    pass
elif env['doxygen'] == 1:
    f = open('Doxyfile_in', "r")
    w = open('Doxyfile', "w")
    for line in f:
        m = re.match(r'^PROJECT_NUMBER.*$', line)
        if m:
            w.write('PROJECT_NUMBER = ' + SWEETSPOT_VER_COMPILATION + '\n')
        else:
            w.write(line)
    os.system('doxygen')
    env.SideEffect('Doxygen', 'Doxygen_in')
else: #build app
    SConscript(['web/SConscript', 'client/SConscript'], exports=['env'] )
