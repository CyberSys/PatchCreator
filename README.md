# PatchCreator.py

A python script to help package update patches for software or directories (linux only).

Recursively compares 2 folders, doing crc checks on all files. New and changed files are
added to a zip, deleted files are written to a shell script and the zip is attached,
creating a single .sh file to distribute.

For the output .sh file, a template system is used (see the shellscript.template file), with
command line args and config file options passed to the template.

Any key defined in the config can be overridden by the command line switches.

### Command line switches

* -c|--conf

Configuration file to use. See patchcreator.conf as a example.

* -o|--old

Old directory, the version to patch. *required unless defined in the config file*

* -n|--new

New directory, the changed version. *required unless defined in the config file*

* --name

Name of the output file. defaults to patch.sh

* --ov

Previous version number. Not required unless used in the template file (or name)

* --nv

New version number. Not required unless used in the template file (or name)

* -t|--template

shell script template file to use. defaults to shellscript.template

* --temp

Temporary directory to use. defaults to ./pc_tmp

* --noclean

Do not clean the temporary directory after running.

* -a|--apply

Apply the patch to the old directory after creation. *for CI pipelines*
