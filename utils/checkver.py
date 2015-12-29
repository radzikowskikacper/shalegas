import os, sys, subprocess, re, getopt

def print_usage(argv):
    """print user help in script mode"""
    print( 'checkver checks the version of installed apt-get packages, pip packages and npm packages' )
    print( "  -d, --dev\t check development packages versions (otherwise production packages)" )
    print( "  -p, --pip\t pip requirements" )
    print( "  -b, --bower-dir\t dir for bower.json" )
    print( "  -h, --help\t show this message" )
    print( 'use: python {} -d -ppip_dev.requirements -b../client'.format( argv[0] ) )
    print( 'use: python {} -ppip_prod.requirements -b../client'.format( argv[0] ) )

#development packages
versions_dev = {'python': ['2.7.5', ''],
                'postgresql' : ['9.1', ''],
                'lighttpd' : ['1.4.31', ''],
                'pip' : [ '1.4.1', '' ],
                'npm' : [ '1.2.18', ''],
                'node' : [ '0.10.15', ''],
                'scons' : [ '2.3.0', ''],
                'postgresql-server-dev-all' : ['9.3', ''],
                'libjpeg-dev' : [ '1.2', ''],
}

#production packages
versions_prod = {'python': ['2.7.5', ''],
                 'postgresql' : ['9.1', ''],
                 'lighttpd' : ['1.4.31', ''],
                 'pip' : [ '1.4.1', '' ],
}



def command_exec(commands):
    """execute system command (subprocess) and return its output"""
    res = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = res.communicate()
    if len(err) > 0:
        print('shell execution error', commands)
    return out

def version_from_oneline_output(commands):
    """execute system command, parse its output to find the N.N.N string"""
    try:
        out = command_exec(commands)
        m = re.search(r'(\d+\.\d+\.\d+)', out)
        if m:
            return m.group(1)
    except:
        pass
    return ''

def printVersions(name, versions):
    """compare and display the installed and required versions"""

    format_string = '%30s %15s %15s %10s'
    print ('\n' + name + '\n' + format_string %('Nazwa', 'Wymagana', 'Znaleziona', 'Status'))
    for key, values in versions.items():
        if len(values[0]) < len(values[1]):
            values[1] = values[1][:len(values[0])]
        if values[0] == values[1]:
            compare = 'OK'
        elif values[1] == '':
            compare = 'Brak!'
        else:
            compare = 'Niezgodna!'
        print (format_string %(key, values[0], values[1], compare))

def aptGetVersions(versions):
    """read the apt-get packages versions"""

    if 'python' in versions.keys():
        versions['python'][1] = sys.version.split(' ')[0]

    if 'postgresql' in versions.keys():
        versions['postgresql'][1] = version_from_oneline_output(['psql', '--version'])

    if 'lighttpd' in versions.keys():
        versions['lighttpd'][1] = version_from_oneline_output(['lighttpd', '-v'])

    if 'pip' in versions.keys():
        versions['pip'][1] = version_from_oneline_output(['pip', '--version'])

    if 'npm' in versions.keys():
        versions['npm'][1] = version_from_oneline_output(['npm', '--version'])

    if 'node' in versions.keys():
        versions['node'][1] = version_from_oneline_output(['node', '--version'])

    if 'scons' in versions.keys():
        versions['scons'][1] = version_from_oneline_output(['scons', '--version'])

    return versions

def npmVersions():
    """read the node package manager package versions"""

    versions = {'bower': ['1.3.1', ''],
    }

    if 'bower' in versions.keys():
        versions['bower'][1] = version_from_oneline_output(['bower', '--version'])

    return versions

def pipVersions(pip_req_filename):
    """create pip package version dict using pip_req_filename, read pip packages versions"""

    pip_versions = {}
    try:
        import pip
        with open(pip_req_filename) as f:
            for line in f:
                m = re.search(r'(.*)==(.*)', line)
                if m:
                    pip_versions[m.group(1)]=[m.group(2),'']

        lst_ver_pip = pip.get_installed_distributions()
        for i in lst_ver_pip:
            if i.project_name in pip_versions:
                pip_versions[i.project_name][1] = i._version

    except ImportError:
        print 'Error, Module pip is required!'

    return pip_versions

def printBowerVersions(bower_dir):
    """run 'bower list' in given dict"""

    print('bower versions')
    curr_dir = os.getcwd()
    os.chdir(bower_dir)
    os.system('bower list')
    os.chdir(curr_dir)



if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_usage(sys.argv)
        sys.exit(2)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:b:dh", ["pip=","bower-dir=","help"])
    except getopt.GetoptError:
        print_usage(sys.argv)
        sys.exit(2)

    pip_req = '../pip_prod.requirements'
    bower_dir = 'client'
    development = False

    for opt, arg in opts:
        if opt in ("-p", "--pip"):
            pip_req = str(arg)
        if opt in ("-b", "--bower-dir"):
            bower_dir = str(arg)
        if opt in ("-h", "--help"):
            print_usage(sys.argv)
            sys.exit(2)
        if opt in ("-d", "--dev"):
            development = True

    if development:
        aptGetVersions(versions_dev)
        printVersions('apt-get packages', versions_dev)
    else:
        aptGetVersions(versions_prod)
        printVersions('apt-get packages', versions_prod)

    pip_versions = pipVersions(pip_req)
    printVersions('pip packages', pip_versions)

    npm_versions = npmVersions()
    printVersions('npm packages', npm_versions)

    printBowerVersions(bower_dir)







