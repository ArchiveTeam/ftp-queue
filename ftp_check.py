import os
import re
import ast
import sys
import shutil
import urllib
import logging

logging.basicConfig(level=logging.DEBUG)

tobechecked = sys.argv[1]
totalsize = 0
maxitemsize = 209715200

if not os.path.exists('items'):
    os.makedirs('items')
if not os.path.exists('archive'):
    os.makedirs('archive')


def fixurl(itemurl):
    """Remove port suffix."""
    if re.search(r'^ftp:\/\/[^\/]+:21\/', itemurl):
        itemurl = itemurl.replace(':21', '', 1)
    return itemurl


def make_initial_dirslist(ftp):
    startdir = '/'
    has_dir = re.search(r'^[^\/]+(\/.+)', ftp)
    if has_dir:
        startdir = has_dir.group(1)
        if not startdir.endswith('/'):
            startdir += '/'
    logging.debug('startdir = ' + startdir)
    return [startdir]


def check_ftp(ftp_str):
    # strip off protocol and trailing slash
    ftp = re.search(r'^(?:ftp:\/\/)?(.+)\/?$', ftp_str).group(1)
    ftp_basename = re.search(r'^([^\/]+)', ftp).group(1)
    output_doc = ftp_basename + '.html'

    logging.info('ftp_basename = ' + ftp_basename)

    os.makedirs(ftp_basename)
    os.chdir(ftp_basename)

    itemftps = []
    itemslist = []
    itemsizes = []
    dirslist = make_initial_dirslist(ftp)
    donedirs = []

    def add_if_missing(s):
        if s not in itemslist:
            itemslist.append(s)
            itemftps.append(ftp_basename)
            itemsizes.append(0)

    def process_dir(dir):
        if dir in donedirs:
            return

        os.system('wget --no-glob --timeout=20 --output-document=' + output_doc +
                  ' "' + dir_url + '"')
        if os.path.isfile(output_doc):
            with open(output_doc, 'r') as index:
                for line in index.read().splitlines():
                    match = re.search(r'<a\s+href="(ftp:\/\/[^\/]+[^"]+)">', line)
                    if match:
                        itemslist.append(match.group(1))
                        itemftps.append(ftp_basename)
                    match = re.search(r'<\/a>.*\(([0-9]+)', line)
                    match2 = re.search(r'<a\s+href="ftp:\/\/[^\/]+([^"]+)">', line)
                    if match:
                        itemsizes.append(int(match.group(1)))
                    elif match2 and ' Directory ' in line:
                        dirslist.append(match2.group(1))
                        itemsizes.append(0)
                    elif match2:
                        itemsizes.append(0)
        donedirs.append(dir)
        if os.path.isfile(output_doc):
            os.remove(output_doc)
        if os.path.isfile('wget-log'):
            os.remove('wget-log')

    while all(dir not in donedirs for dir in dirslist):
        for dir in dirslist:
            dir = dir.replace('&#32;', '%20').replace('&amp;', '&')
            if re.search(r'&#[0-9]+;', dir):
                raise Exception(dir)
            dir = dir.replace('#', '%23')
            dir_url = 'ftp://' + ftp_basename + dir
            logging.info('dir_url = ' + dir_url)

            add_if_missing(dir_url)
            add_if_missing(dir_url + './')
            add_if_missing(dir_url + '../')

            # break directory loops
            for match in re.findall(r'([^\/]+)', dir):
                if '/' + match + '/' + match + '/' + match + '/' + match + '/' + match in dir:
                    break
            else:
                process_dir(dir)
    os.chdir('..')
    shutil.rmtree(ftp_basename)

    make_output(zip(itemftps, itemslist, itemsizes))

    try:
        urllib.urlopen('ftp://' + ftp_basename + '/NONEXISTINGFILEdgdjahxnedadbacxjbc/')
    except Exception as error:
        dir_not_found = str(error).replace('[Errno ftp error] ', '')
        print(dir_not_found)

    try:
        urllib.urlopen('ftp://' + ftp_basename + '/NONEXISTINGFILEdgdjahxnedadbacxjbc')
    except Exception as error:
        file_not_found = str(error).replace('[Errno ftp error] ', '')
        print(file_not_found)

    if os.path.isfile('items/' + ftp_basename + '_dir_not_found'):
        os.remove('items/' + ftp_basename + '_dir_not_found')
    if os.path.isfile('items/' + ftp_basename + '_file_not_found'):
        os.remove('items/' + ftp_basename + '_file_not_found')

    with open('items/' + ftp_basename + '_dir_not_found', 'w') as file:
        file.write(dir_not_found)
    with open('items/' + ftp_basename + '_file_not_found', 'w') as file:
        file.write(file_not_found)

    if not tobechecked == 'to_be_rechecked':
        with open('to_be_rechecked', 'a') as file:
            if os.path.isfile('to_be_checked'):
                file.write('\n' + ftp)
            else:
                file.write(ftp)


def make_output(totalitems):
    global totalsize
    itemsize = 0
    itemlinks = 0
    archive_file = 'archive/' + totalitems[0][0]
    archive_data_file = archive_file + '-data'

    if os.path.isfile(archive_file):
        with open(archive_file) as file:
            archivelist = [list(ast.literal_eval(line)) for line in file]
    else:
        archivelist = []

    if os.path.isfile(archive_data_file):
        with open(archive_data_file, 'r') as file:
            itemnum = int(file.read()) + 1
    else:
        itemnum = 0

    for item in totalitems:
        match = re.search(r'^(ftp:\/\/.+\/)[^\/]+\/', item[1])
        if match and (item[0], match.group(1), 0) not in totalitems:
            match = re.search(r'^(.+\/)[^\/]+\/', item[1]).group(1)
            totalitems.append((item[0], match, 0))
            totalitems.append((item[0], match + './', 0))
            totalitems.append((item[0], match + '../', 0))

    newitems = []
    for item in totalitems:
        itemurl = fixurl(item[1])
        if '&amp;' in itemurl or [item[2], itemurl] not in archivelist:
            newitems.append(item)

    for item in newitems:
        itemdir = re.search(r'^(ftp:\/\/.+\/)', item[1]).group(1)
        while True:
            if (item[0], itemdir, 0) not in newitems:
                newitems.append((item[0], itemdir, 0))
            if re.search(r'^ftp:\/\/[^\/]+\/$', itemdir):
                break
            itemdir = re.search(r'^(ftp:\/\/.+\/)[^\/]+\/', itemdir).group(1)
        itemurl = fixurl(item[1])
        with open('items/' + item[0] + '_' + str(itemnum), 'a') as file:
            file.write(itemurl + '\n')
            itemsize += item[2]
            totalsize += item[2]
            itemlinks += 1
            if itemsize > maxitemsize or newitems[len(newitems)-1] == item:
                file.write('ITEM_NAME: ' + item[0] + '_' + str(itemnum) + '\n')
                file.write('ITEM_TOTAL_SIZE: ' + str(itemsize) + '\n')
                file.write('ITEM_TOTAL_LINKS: ' + str(itemlinks) + '\n')
                itemnum += 1
                itemsize = 0
                itemlinks = 0
        if not [item[2], itemurl] in archivelist:
            quote = '"' if "'" in itemurl else "'"
            with open('archive/' + item[0], 'a') as file:
                file.write(str(item[2]) + ", " + quote + itemurl + quote + "\n")
        with open(archive_data_file, 'w') as file:
            if os.path.isfile('items/' + item[0] + '_' + str(itemnum-1)):
                file.write(str(itemnum-1))


with open(tobechecked, 'r') as file:
    ftps = file.read().splitlines()
    for ftp in ftps:
        check_ftp(ftp)

print(totalsize)
