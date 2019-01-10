# PatchCreator.py

A python script to help package update patches for software or directories (linux only).

Recursively compares 2 folders, doing crc checks on all files. New and changed files are
added to a zip, deleted files are written to a shell script and the zip is attached,
creating a single .sh file to distribute.

For the output .sh file, a template system is used (see {shellscript.template}), with
command line args and config file options passed to the template.

Any key defined in the config can be overridden by the command line switches.

### Command line switches

* -c|--conf         config file to use.

* -o|--old          old directory, the version to patch. required unless defined in the config file.

* -n|--new          new directory, the changed version. required unless defined in the config file.

* --name            name of the project

* --ov              previous version number

* --nv              new version number

* -t|--template     shell script template file to use

* --temp            temporary directory to use

* --noclean         do not clean the tempory directory after

* -a|--apply        apply the patch to the old directory after creation. for CI pipelines
