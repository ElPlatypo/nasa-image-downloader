import requests
import re
import os
import pandas as pd
import datetime
import json

dirpath = os.path.dirname(os.path.abspath(__file__))
dbpath = dirpath + '/TSVdatabase'
df = pd.DataFrame()

def main():
    print('Welcome to the NASA ISS image scraper')
    print('loading database')
    Loadb()
    c = True
    while c == True:
        i = input('select operation (d download raw db, b build true db, gt group for delta-time, ds download sequence q quit program)\n')
        if i == 'd':
            Fetchdb()
            Buildb()
        elif i == 'b':
            Buildb()
        elif i == 'gt':
            i2 = int(input('please select delta-time in seconds between frames to group\n'))
            i3 = int(input('select minimum number of consecutive frames\n'))
            GroupTime(i2,i3)
        elif i == 'ds':
            DownloadSequence()
        elif i == 'q':
            exit()
        else:
            print('unrecognised input')


def Fetchdb():
    baseurl = 'https://eol.jsc.nasa.gov/SearchPhotos/mrf.pl?scope=both&MRFList=ISS'
    basetsv = 'https://eol.jsc.nasa.gov/SearchPhotos/GetTSVFromQueryResults.pl?results='
    if os.path.isdir(dbpath) == False:
        try:
            os.mkdir(dbpath)
        except OSError:
            print('error creating database directory... aborting')
            exit()
    rng = CompileReq()
    print('downloading tsv chunks, this will take a while')
    for mission in range(rng[0], rng[1]+1):
        if mission <= 9:
            url = baseurl + '00%d'%mission 
        else:
            url = baseurl + '0%d'%mission   
        frame = 1
        overflowcount = 0
        newfile = open(dirpath + '/TSVdatabase/ISS{}-E.tsv'.format(mission), 'w')
        for chunk in range(1000):
            chunkurl = url + '-E-{}-'.format(frame)
            frame = frame + 999
            chunkurl = chunkurl + str(frame)
            frame += 1
            print("fetching tsv download URL for ISS{} chunk {}... ".format(mission, chunk), end='', flush=True)
            urlr = requests.get(chunkurl)
            if urlr.status_code != 200:
                print('FAILED with error code {}'.format(mission, chunk, urlr.status_code))
            else:
                print('SUCCESS')
                rule = re.compile(r'Forward Page for (?P<idgroup>[0-9]+) MRF Query')
                pageid = rule.search(urlr.text)['idgroup']
                print('downloading tsv... ', end = '', flush = True)
                tsvr = requests.get(basetsv + pageid)
                if tsvr.status_code != 200:
                    print('FAILED with error code {}'.format(mission, chunk, urlr.status_code))
                else:
                    if len(tsvr.text) > 1000:
                        overflowcount = 0
                        print('SUCCESS')
                        newfile.write(tsvr.text)
                    else:
                        overflowcount += 1
                        print('chunk was empty! skipping to next chunk {}/10'.format(overflowcount))
                    if overflowcount > 9:
                        overflowcount = 0
                        break
        newfile.close()

def Buildb():
    global df
    df = pd.DataFrame() #wipe currently loaded database
    print('building raw db with tsv files')
    if os.path.isfile(dirpath + '/db.pkl') == True:
        os.remove(dirpath + '/db.pkl')
    if len(os.listdir(dbpath)) == 0:
        if input('unable to find raw tsv files, download new ones? (y/n)\n') == 'y' or 'Y':
            Fetchdb()
        else:
            return
    for tsvfile in os.walk(dbpath).__next__()[2]: #iterate on all files inside the directory
        tmpdf = pd.read_csv(dbpath + '/' + tsvfile, sep='\t')
        df = df.append(tmpdf, ignore_index=True)
    Cleandb()
    df.to_pickle(dirpath + '/db.pkl')

def Cleandb():
    global df
    print('cleaning up db')
    df = df[df.mission != 'mission'] #remove all title rows
    df = df[df.mission.str.contains('ISS', na=False)] # removes frames without mission
    df = df[df['Photo Date'].notna()]
    df = df[df['Photo Time GMT'].notna()]
    df = df[df['Photo Date'].str.contains('_') != True]
    df = df[df['Photo Time GMT'].str.contains('_') != True]
    df = df.sort_values(['Photo Date', 'Photo Time GMT'])
    df = df.reset_index(drop=True)
    df['Photo Time Delta'] = (pd.to_datetime(df['Photo Date'] + df['Photo Time GMT']) - pd.to_datetime(df['Photo Date'] + df['Photo Time GMT']).shift())

def Loadb():
    global df
    if os.path.isfile(dirpath + '/db.pkl') == False:
        if input('unable to find database, generate a new one? (y/n)\n') == 'y' or 'Y':
            Buildb()
        else:
            print('database NOT loaded!')
            return
    df = pd.read_pickle(dirpath + '/db.pkl')
    print('Database loaded')

def CompileReq():
    c = True
    while c == True:
        i = input('please select ISS mission to download (help for more info)\n')
        if i == 'help':
            print('Select the mission, range, or all to download tsvs from \nexample: ISS 1 or ISS 13-48 or all')
        elif i.startswith('ISS') == True:
            return Range(i[4:])
            c = False
        elif i.startswith('all'):
            return [1, 64]
            c = False
        else:
            print('invalid input')

def Range(rng):
    if '-' not in rng:
        return [int(rng), int(rng)+1]
    else:
        r = rng.split('-')
        return [int(r[0]), int(r[1])]

def GroupTime(delta, size):
    searchpath = dirpath + '/search_delta{}_quantity{}'.format(delta, size)
    if os.path.isdir(searchpath) == False:
        try:
            os.mkdir(searchpath)
        except OSError:
            print('error creating search result directory... aborting')
            exit()
    groups = {}
    d = datetime.timedelta(seconds=delta)
    newgroup = []
    n = 1
    for index, row in df.iterrows():
        if row['Photo Time Delta'] <= d:
            newgroup.append(row['mission'] + '-E-' + row['frame'].split()[0])
        else:
            if len(newgroup) > size:
                groups['group {}'.format(n)] = newgroup
                n += 1
            newgroup = []
    print('found {} group/s matching criteria'.format(n))
    with open(searchpath + '/search.json', 'w') as js:
        json.dump(groups, js)
    i = input('download preview for selected groups? (y/n)\n')
    if i == 'y' or 'Y':
        for group in groups.keys():
            print(group)
            img = open(searchpath + '/group{}_preview'.format(group.split()[1]) + '.jpg', 'wb')
            img.write(DownloadImg(groups[group][0][:6], groups[group][0][9:], 'small'))
            img.close()

def DownloadSequence():
    i = input('please select search folder to load groups from (delta,quantity separated by a space)\n').split()
    i2 = input('choose group to download\n')
    i3 = input('small or large files? (small/large)\n')
    path = dirpath + '/search_delta{}_quantity{}'.format(i[0], i[1])
    if os.path.isdir(path) == False:
        print('unable to locate search_delta{}_quantity{}'.format(i[0], i[1]))
        return
    groups = json.load(open(path + '/search.json', 'r'))
    if os.path.isdir(path + '/group{}'.format(i2)) == False:
        try:
            os.mkdir(path + '/group{}'.format(i2))
        except OSError:
            print('error creating group directory... aborting')
            exit()
    i4 = input('downloading {} files, confirm? (y/n)'.format(len(groups['group {}'.format(i2)])))
    if i4 == 'y' or 'Y':
        for frame in groups['group {}'.format(i2)]:
            img = open(path + '/group{}/{}'.format(i2, frame) + '.jpg', 'wb')
            img.write(DownloadImg(frame[:6], frame[9:], i3))
            img.close()


def DownloadImg(mission, frame, size):
    img = requests.get('https://eol.jsc.nasa.gov/DatabaseImages/ESC/{}/{}/{}-E-{}.JPG'.format(size, mission, mission, frame))
    if img.status_code == 200:
        print('downloaded {}-{}-{}'.format(mission, frame, size))
        return img.content
    else:
        print('error while downloading {}-{}-{}'.format(mission, frame, size))

if __name__ == '__main__':
    main()