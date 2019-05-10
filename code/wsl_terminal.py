import sys, time, os


class BashConfigure:
    def __init__(self):
        self.dirhome = os.path.abspath(os.path.dirname("__file__"))
        self.diruser = os.path.abspath(os.path.expanduser('~'))
        self.unix = sys.platform[:3] != 'win' and True or False
        self.temp = os.environ.get('temp', os.environ.get('tmp', '/tmp'))
        self.tick = float(time.time()) % 100
        if self.unix:
            temp = os.environ.get('tmp', '/tmp')
            if not temp:
                temp = '/tmp'
            folder = os.path.join(temp, 'runner/folder')
            if not os.path.exists(folder):
                try:
                    os.makedirs(folder)
                except:
                    folder = ''
            if folder:
                self.temp = folder
                try:
                    os.chmod(self.temp)
                except:
                    pass
        self.temp = os.path.join(self.temp, 'winex_%02d.cmd' % self.tick)
        self.cygwin = ''
        self.GetShortPathName = None
        self.GetFullPathName = None
        self.GetLongPathName = None
        self.ShellExecute = None
        self.kernel32 = None
        self.textdata = None
        self.filter = None
        self.filter_mode = ''
        self.encoding = None

    def rename_temp(self):
        self.tick = float(time.time()) % 100
        self.temp = os.path.join(self.temp, 'winex_%02d.cmd' % self.tick)

    def win32_wsl_open_bash(self, title, script, profile=None):
        bash = self.win32_wsl_locate(profile)
        if not bash:
            return -1, None
        # I created this while loop because for some reason I do not get access to write over / delete a specific temp
        # file so I decided to just rename the temp file and keep trying.
        while True:
            try:
                with open(self.temp, 'wb') as fp:
                    fp.write('#! /bin/bash\n'.encode('utf-8'))
                    path = self.win2wsl(os.getcwd())
                    fp.write(('cd %s\n' % self.unix_escape(path)).encode('utf-8'))
                    for line in script:
                        fp.write(('%s\n' % line).encode('utf-8'))
                break
            except PermissionError:
                self.rename_temp()
        if not profile:
            command = '--login -i "' + self.win2wsl(self.temp) + '"'
        else:
            command = 'run bash --login -i "' + self.win2wsl(self.temp) + '"'
        self.win32_shell_execute('open', bash, command, os.getcwd())
        return 0

    def win32_wsl_locate(self, profile=None):
        if not self.win32_detect_win10():
            return None

        if profile:
            name = profile + '.exe'
            for path in os.environ.get('PATH', '').split(';'):
                fn = os.path.join(path, name)
                if os.path.exists(fn):
                    return name
            return None

        root = os.environ.get('SystemRoot', None)

        if not root:
            return None
        system32 = os.path.join(root, 'System32')
        bash = os.path.join(system32, 'bash.exe')
        if os.path.exists(bash):
            return bash
        system32 = os.path.join(root, 'SysNative')
        bash = os.path.join(system32, 'bash.exe')

        if os.path.exists(bash):
            return bash
        return None

    def win32_detect_win10(self):
        try:
            import winreg
            path = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion'
            data = self.win32_reg_read(winreg.HKEY_LOCAL_MACHINE, path)
        except:
            return False
        version = data.get('CurrentMajorVersionNumber', (0, 0))
        if version[1] >= 10:
            return True
        return False

    def win32_reg_read(self, keyname, path):
        try:
            import winreg
            mode = winreg.KEY_READ | winreg.KEY_WOW64_64KEY
            key = winreg.OpenKey(keyname, path, 0, mode)
            count = winreg.QueryInfoKey(key)[0]
        except:
            return None
        data = {}
        for i in range(count):
            try:
                name, value, tt = winreg.EnumValue(key, i)
            except OSError as e:
                break
            data[name] = (tt, value)
        return data

    def win2wsl(self, path):
        save = path
        path = self.win32_path_casing(path)
        if not path:
            return ''
        if len(path) < 3:
            return ''
        return '/mnt/%s%s' % (path[0].lower(), path[2:].replace('\\', '/'))

    def win32_path_casing(self, path):
        if not path:
            return ''
        path = os.path.abspath(path)
        if self.unix:
            return path
        path = path[:1].upper() + path[1:]
        return self.win32_path_long(self.win32_path_short(path))

    def win32_path_long(self, path):
        if not path:
            return ''
        path = os.path.abspath(path)
        if self.unix:
            return path
        self._win32_load_kernel()
        if not self.GetLongPathName:
            try:
                import ctypes
                from ctypes import wintypes

                self.GetLongPathName = ctypes.windll.kernel32.GetLongPathNameW
                self.GetLongPathName.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
                self.GetLongPathName.restype = wintypes.DWORD

            except:
                pass
        if not self.GetLongPathName:
            return path
        retval = self.GetLongPathName(path, self.textdata, 2048)
        longpath = self.textdata.value
        if retval <= 0:
            return ''
        return longpath

    def win32_path_short(self, path):
        if not path:
            return ''
        path = os.path.abspath(path)
        if self.unix:
            return path
        self._win32_load_kernel()
        if not self.GetShortPathName:
            try:
                import ctypes
                from ctypes import wintypes

                self.GetShortPathName = ctypes.windll.kernel32.GetShortPathNameW
                self.GetShortPathName.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
                self.GetShortPathName.restype = wintypes.DWORD

            except:
                pass
        if not self.GetShortPathName:
            return path

        retval = self.GetShortPathName(path, self.textdata, 2048)
        shortpath = self.textdata.value
        if retval <= 0:
            import ctypes
            print('ERROR(%d): %s' % (ctypes.GetLastError(), path))
            return ''
        return shortpath

    def _win32_load_kernel(self):
        if self.unix:
            return False
        import ctypes
        if not self.kernel32:
            self.kernel32 = ctypes.windll.LoadLibrary("kernel32.dll")
        if not self.textdata:
            # self.textdata = ctypes.create_string_buffer(2048)
            self.textdata = ctypes.create_unicode_buffer(2048)
        ctypes.memset(self.textdata, 0, 2048)
        return True

    def unix_escape(self, argument, force=False):
        argument = argument.replace('\\', '\\\\')
        argument = argument.replace('"', '\\"')
        argument = argument.replace("'", "\\'")
        return argument.replace(' ', '\\ ')

    def win32_shell_execute(self, op, filename, parameters, cwd=None):
        if self.unix:
            return False
        if not cwd:
            cwd = os.getcwd()
        self._win32_load_kernel()
        if not self.ShellExecute:
            try:
                import ctypes
                from ctypes import wintypes
                self.shell32 = ctypes.windll.LoadLibrary('shell32.dll')

                self.ShellExecute = ctypes.windll.shell32.ShellExecuteW

                args = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
                args += [wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.c_int32]

                self.ShellExecute.argtypes = args
                self.ShellExecute.restype = wintypes.HINSTANCE
            except:
                pass
        if not self.ShellExecute:
            return False
        nShowCmd = 5
        self.ShellExecute(None, op, filename, parameters, cwd, nShowCmd)
        return True