import os


def get_windows_filename(filename):
    """
    Given a Linux filepath it will create the Windows version.
    """
    # remove the single quotes if added
    if filename[0] == "'" and filename[-1] == "'":
        filename = filename[1:-1]

    filename_split = filename.split('/')
    mnt_i = filename_split.index('mnt')

    drive_letter = filename_split[mnt_i + 1].upper()

    remaining = '\\'.join(list(filename_split[mnt_i + 2:]))

    return '%s:\\%s' % (drive_letter, remaining)


def get_ubuntu_path(filepath):
    """
    Given a Windows filepath it will create the Linux version.
    """
    # get the drive letter

    drive_letter_i = filepath.find(':/')

    if drive_letter_i == -1:
        drive_letter_i = filepath.find(':\\')

    drive_letter = filepath[:drive_letter_i].lower()

    i = 1
    while drive_letter_i + i == '/':
        i += 1

    remaining_path = filepath[drive_letter_i + i + 1:]
    linux_path = '/mnt/%s/%s' % (drive_letter, remaining_path)

    # add single quotes so linux can understand the special characters
    if '(' in linux_path or ')' in linux_path:
        linux_path = "'%s'" % linux_path

    return os.path.normpath((linux_path)).replace('\\', '/')