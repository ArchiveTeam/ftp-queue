# ftp-queue

`ftp-check.py` is a script used to create item lists for ftp-grab.

How to run
----------
Clone the repo. cd into the repo and create a file with a list of FTPs you want to check.

Use `python ftp-check.py listofftpstobechecked` to run the discovery. If you scan a FTP that has already been scanned and has an archive file in the `archive` dir, only new files or files with a different size will be added to the item lists.

If you have scanned a FTP site, let Archive Team know in #effteepee on IRC efnet. Provide the itemlistfiles from the `items` dir and the new files from the `archive` dir.
