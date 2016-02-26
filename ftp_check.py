import os
import re
import ast
import sys
import shutil
import urllib

tobechecked = sys.argv[1]
totalsize = 0
maxitemsize = 209715200

if not os.path.exists('items'):
    os.makedirs('items')
if not os.path.exists('archive'):
    os.makedirs('archive')

def fixurl(itemurl):
    if re.search(r'^ftp:\/\/[^\/]+:21\/', itemurl):
        itemurl = itemurl.replace(':21', '', 1)
    return itemurl

with open(tobechecked, 'r') as file:
    ftps = file.read().splitlines()
    for ftp in ftps:
        ftp = re.search(r'^(?:ftp:\/\/)?(.+)\/?$', ftp).group(1)
        os.makedirs(re.search(r'^([^\/]+)', ftp).group(1))
        os.chdir(re.search(r'^([^\/]+)', ftp).group(1))
        itemftps = []
        itemslist = []
        itemsizes = []
        startdir = '/'
        if re.search(r'^[^\/]+\/.+', ftp):
            startdir = re.search(r'^[^\/]+(\/.+)', ftp).group(1)
            if not startdir.endswith('/'):
                startdir += '/'
        dirslist = [startdir]
        donedirs = []
        while all(dir not in donedirs for dir in dirslist):
            for dir in dirslist:
                dir = dir.replace('&#32;', '%20').replace('&amp;', '&')
                if re.search(r'&#[0-9]+;', dir):
                    raise Exception(dir)
                dir = dir.replace('#', '%23')
                if not 'ftp://' + re.search(r'^([^\/]+)', ftp).group(1) + dir in itemslist:
                    itemslist.append('ftp://' + re.search(r'^([^\/]+)', ftp).group(1) + dir)
                    itemftps.append(re.search(r'^([^\/]+)', ftp).group(1))
                    itemsizes.append(0)
                if not 'ftp://' + re.search(r'^([^\/]+)', ftp).group(1) + dir + './' in itemslist:
                    itemslist.append('ftp://' + re.search(r'^([^\/]+)', ftp).group(1) + dir + './')
                    itemftps.append(re.search(r'^([^\/]+)', ftp).group(1))
                    itemsizes.append(0)
                if not 'ftp://' + re.search(r'^([^\/]+)', ftp).group(1) + dir + '../' in itemslist:
                    itemslist.append('ftp://' + re.search(r'^([^\/]+)', ftp).group(1) + dir + '../')
                    itemftps.append(re.search(r'^([^\/]+)', ftp).group(1))
                    itemsizes.append(0)
                for match in re.findall(r'([^\/]+)', dir):
                    if '/' + match + '/' + match + '/' + match + '/' + match + '/' + match in dir:
                        break
                else:
                    if not dir in donedirs:
                        os.system('wget --no-glob --timeout=20 --output-document=' + re.search(r'^([^\/]+)', ftp).group(1) + '.html "ftp://' + re.search(r'^([^\/]+)', ftp).group(1) + dir + '"')
                        if os.path.isfile(re.search(r'^([^\/]+)', ftp).group(1) + '.html'):
                            with open(re.search(r'^([^\/]+)', ftp).group(1) + '.html', 'r') as index:
                                for line in index.read().splitlines():
                                    if re.search(r'<a\s+href="ftp:\/\/[^\/]+[^"]+">', line):
                                        itemslist.append(re.search(r'<a\s+href="(ftp:\/\/[^\/]+[^"]+)">', line).group(1))
                                        itemftps.append(re.search(r'^([^\/]+)', ftp).group(1))
                                    if re.search(r'<\/a>.*\(', line):
                                        itemsizes.append(int(re.search(r'<\/a>.*\(([0-9]+)', line).group(1)))
                                    elif re.search(r'<a\s+href="ftp:\/\/[^\/]+([^"]*)">', line) and ' Directory ' in line:
                                        dirslist.append(re.search(r'<a\s+href="ftp:\/\/[^\/]+([^"]+)">', line).group(1))
                                        itemsizes.append(0)
                                    elif re.search(r'<a\s+href="ftp:\/\/[^\/]+([^"]*)">', line):
                                        itemsizes.append(0)
                        donedirs.append(dir)
                        if os.path.isfile(re.search(r'^([^\/]+)', ftp).group(1) + '.html'):
                            os.remove(re.search(r'^([^\/]+)', ftp).group(1) + '.html')
                        if os.path.isfile('wget-log'):
                            os.remove('wget-log')
        os.chdir('..')
        shutil.rmtree(re.search(r'^([^\/]+)', ftp).group(1))
        totalitems = zip(itemftps, itemslist, itemsizes)
        archivelist = []
        newitems = []
        itemsize = 0
        itemnum = 0
        itemlinks = 0
        if os.path.isfile('archive/' + totalitems[0][0]):
            with open('archive/' + totalitems[0][0]) as file:
                archivelist = [list(ast.literal_eval(line)) for line in file]
        if os.path.isfile('archive/' + totalitems[0][0] + '-data'):
            with open('archive/' + totalitems[0][0] + '-data', 'r') as file:
                itemnum = int(file.read()) + 1
        for item in totalitems:
            if re.search(r'^(ftp:\/\/.+\/)[^\/]+\/', item[1]):
                if not (item[0], re.search(r'^(ftp:\/\/.+\/)[^\/]+\/', item[1]).group(1), 0) in totalitems:
                    totalitems.append((item[0], re.search(r'^(.+\/)[^\/]+\/', item[1]).group(1), 0))
                    totalitems.append((item[0], re.search(r'^(.+\/)[^\/]+\/', item[1]).group(1) + './', 0))
                    totalitems.append((item[0], re.search(r'^(.+\/)[^\/]+\/', item[1]).group(1) + '../', 0))
        for item in totalitems:
            itemurl = fixurl(item[1])
            if '&amp;' in itemurl or not [item[2], itemurl] in archivelist:
                newitems.append(item)
        for item in newitems:
            itemdir = re.search(r'^(ftp:\/\/.+\/)', item[1]).group(1)
            while True:
                if not (item[0], itemdir, 0) in newitems:
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
                with open('archive/' + item[0], 'a') as file:
                    if "'" in itemurl:
                        file.write(str(item[2]) + ", \"" + itemurl + "\"\n")
                    else:
                        file.write(str(item[2]) + ', \'' + itemurl + '\'\n')
            with open('archive/' + totalitems[0][0] + '-data', 'w') as file:
                if os.path.isfile('items/' + item[0] + '_' + str(itemnum-1)):
                    file.write(str(itemnum-1))
        try:
            urllib.urlopen('ftp://' + re.search(r'^([^\/]+)', ftp).group(1) + '/NONEXISTINGFILEdgdjahxnedadbacxjbc/')
        except Exception as error:
            dir_not_found = str(error).replace('[Errno ftp error] ', '')
            print(dir_not_found)

        try:
            urllib.urlopen('ftp://' + re.search(r'^([^\/]+)', ftp).group(1) + '/NONEXISTINGFILEdgdjahxnedadbacxjbc')
        except Exception as error:
            file_not_found = str(error).replace('[Errno ftp error] ', '')
            print(file_not_found)

        if os.path.isfile('items/' + re.search(r'^([^\/]+)', ftp).group(1) + '_dir_not_found'):
            os.remove('items/' + re.search(r'^([^\/]+)', ftp).group(1) + '_dir_not_found')
        if os.path.isfile('items/' + re.search(r'^([^\/]+)', ftp).group(1) + '_file_not_found'):
            os.remove('items/' + re.search(r'^([^\/]+)', ftp).group(1) + '_file_not_found')

        with open('items/' + re.search(r'^([^\/]+)', ftp).group(1) + '_dir_not_found', 'w') as file:
            file.write(dir_not_found)
        with open('items/' + re.search(r'^([^\/]+)', ftp).group(1) + '_file_not_found', 'w') as file:
            file.write(file_not_found)

        if not tobechecked == 'to_be_rechecked':
            with open('to_be_rechecked', 'a') as file:
                if os.path.isfile('to_be_checked'):
                    file.write('\n' + ftp)
                else:
                    file.write(ftp)

print(totalsize)
