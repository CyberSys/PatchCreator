# -*- coding: utf-8 -*-

# =============================================================================
#
#    Copyright (C) 2016  Fenris_Wolf, YSPStudios
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# =============================================================================

import shutil
import os
from os.path import join, isdir, dirname, exists
import time
import ConfigParser
import subprocess
from zlib import crc32
import argparse

args = None
logfile = None
config = None

def init():
    global args, logfile, config
    defaults = {
        'name': 'patch.sh',
        'template' : "shellscript.template",
        'temp': "pc_tmp",
        'old': None,
        'new': None,
        'noclean' : False,
        'apply' : False,
        'oldver' : None,
        'newver' : None,
    }


    parser = argparse.ArgumentParser(description="""Compares 2 folders (A and B) and builds a shell script/zip file for updating A to B.
     Useful for creating software update patches for linux systems.
     """)
    parser.add_argument('-c', '--conf', dest='conf',
                        help='config file to use.')
    parser.add_argument('-o', '--old', dest='old',
                        help='old directory, the version to patch. required unless defined in the config file.')
    parser.add_argument('-n', '--new', dest='new',
                        help='new directory, the changed version. required unless defined in the config file.')
    parser.add_argument('--name', dest='name',
                        help='name of the project')
    parser.add_argument('--ov', dest='oldver',
                        help='previous version number')
    parser.add_argument('--nv', dest='newver',
                        help='new version number')
    parser.add_argument('-t', '--template', dest='template',
                        help='shell script template file to use')
    #parser.add_argument('--maintainer', dest='maintainer',
    #                    help='maintainer/publisher of the update patch')
    #parser.add_argument('--project', dest='project',
    #                    help='software/project name')
    #parser.add_argument('--company', dest='company',
    #                    help='software production company')
    parser.add_argument('--temp', dest='temp',
                        help='temporary directory to use')
    parser.add_argument('--noclean', dest='noclean', action='store_true',
                        help='do not clean the tempory directory after')
    parser.add_argument('-a', '--apply', dest='apply', action='store_true',
                        help='apply the patch to the old directory after creation. for CI pipelines')

    args = parser.parse_args()
    config = ConfigParser.ConfigParser(defaults)
    config.add_section('Project')
    config.add_section('Template')
    if args.conf:
        config.read(args.conf)
    for key in ['name', 'old', 'new', 'template', 'temp', 'oldver', 'newver']:
        if getattr(args, key) is None:
            setattr(args, key, config.get('Project', key))

    for key in ['noclean', 'apply']:
        if getattr(args, key) is None:
            setattr(args, key, config.getboolean('Project', key))

    logfile = open("patchcreator.log", "w")

def validate_settings():
    if not isdir(args.old):
        out("Invalid 'old' path: " + args.old)
        exit(1)
    if not isdir(args.new):
        out("Invalid 'new' path: " + args.new)
        exit(1)

    if not isdir(args.temp):
        out("PatchCreator: Creating temp directory")
        # TODO: error checking
        os.makedirs(args.temp)

# =============================================================================
# Basic functions
def out(text):
    """Basic logging function"""
    print text
    logfile.write(text + "\n")


def list_directory(path):
    """Recursively lists all files in a directory"""
    result = []
    plen = len(path)+1
    result = [join(dp[plen:], f) for dp, _, filenames in os.walk(path) for f in filenames]
    result.sort()
    return result


def copy_file(source_folder, dest_folder, path):
    """Copies a file, creating the destination path if needed"""
    #common.logger("Copying %s" % path)
    new_path = join(dest_folder, path)
    ori_path = join(source_folder, path)
    if not exists(dirname(new_path)):
        os.makedirs(dirname(new_path))
    shutil.copy2(ori_path, new_path)


def get_file_crc(path):
    """Returns the CRC value for the specified file"""
    fih = open(path, 'rb')
    result = "%x" % (crc32(fih.read()) & 0xFFFFFFFF)
    fih.close()
    return result


def get_directory_crcs(basepath, lowercase=False):
    """Recursively calculates the crc values for all files in a directory. Returns a dict."""
    result = {}
    for file_name in list_directory(basepath):
        if lowercase:
            file_name = file_name.lower()
        result[file_name] = get_file_crc(join(basepath, file_name))
    return result


def create_zip():
    out("Compressing patch...")
    cwd = os.getcwd()
    os.chdir(args.temp)
    result = subprocess.call(['zip', '-r', "pc_tmp", "."])
    os.chdir(cwd)
    if result == 0:
        return join(args.temp, "pc_tmp.zip")
    return None

def format_script(deleted_files):
    name = args.name.format(oldver=args.oldver, newver=args.newver, time=int(time.time()))
    tmp = open(args.template)
    text = tmp.read()
    tmp.close()
    items = {}
    for key in config.options('Template'):
        arg = getattr(args, key, None)
        items[key] = arg != None and arg or config.get('Template', key)
    items['ctime'] = time.ctime()
    items['name'] = name
    items['deleted_files'] = "\n".join(['rm "%s"' % x for x in deleted_files])
    text = text.format(**items)
    return text

def create_script(deleted_files, zipfile):

    out("Creating patch script file...")
    text = format_script(deleted_files)

    name = args.name.format(oldver=args.oldver, newver=args.newver, time=int(time.time()))
    fih = open(name, "wb") #open in binary so we can append our zip
    fih.write(text+"\n")

    if zipfile:
        out("Merging...")
        zfi = open(zipfile, "rb")
        fih.write(zfi.read())
        subprocess.call(['rm', zipfile])

    fih.close()
    subprocess.call(['chmod', '+x', name])
    if args.noclean != True:
        subprocess.call(['rm', '-r', args.temp])

#==============================================================================
# MAIN CODE

def main():
    changed_files = 0
    new_files = 0
    deleted_files = []

    out("PatchCreator: Generating old file crcs...")
    old_crcs = get_directory_crcs(args.old)

    out("PatchCreator: Generating new version crcs...")
    new_crcs = get_directory_crcs(args.new)


    for filename in new_crcs:
        if not old_crcs.has_key(filename): #new file
            # copy to the patch
            new_files += 1
            out("New File: " +filename)
            copy_file(args.new, args.temp, filename)
            continue
        if new_crcs[filename] != old_crcs[filename]: # changed file
            # copy to the patch
            changed_files += 1
            out("Changed File: " +filename)
            copy_file(args.new, args.temp, filename)
            continue

    for filename in old_crcs:
        if not new_crcs.has_key(filename): #deleted file
            deleted_files.append(filename)
            out("Deleted File: " +filename)
    out("")
    out("")
    out("----------------------------------------")
    out("New: %s, Changed: %s, Deleted: %s" % (new_files, changed_files, len(deleted_files)))
    out("")
    zipfile = create_zip()
    if zipfile or deleted_files:
        create_script(deleted_files, zipfile)

init()
##print format_script([])
main()
logfile.close()
