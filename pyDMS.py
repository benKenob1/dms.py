#!/usr/bin/env python3

import argparse
import sqlite3
import datetime
import os
from shutil import copyfile
'''
#########################################################
#config part
#########################################################
'''
config = {
    'managedDir': '/home/benni/Dokumente/DMS/',
    'newFilesDir': '/home/benni/Dokumente/DMS/new/',
    'dbTyp': 'SQLight',
    'dbFile': '/home/benni/Dokumente/pyDMS.sql'
}


class newFile(object):
    '''
    Instances of this class are look for new File
    make a list of the files with all tags
    clean the newsDir
    '''

    def __init__(self, newsDir):
        self.dir = newsDir
        self.newFileList = []

        self.__createList()

    def __createList(self):
        for root, dir, files in os.walk(self.dir):
            for file in files:
                try:
                    newItem = self.__filterItem(file)
                    if newItem:
                        self.newFileList.append(newItem)
                except ValueError as err:
                    print(err)

    def __filterItem(self, filename):
        # gets a filename, tries to create a dict with the tags and returns it
        fileData = {"filename": filename,
                    "date": "",
                    "tags":  "",
                    "type":  "",
                    "place": ""}
        try:
            (fileData["date"],
             fileData["tags"],
             fileData["type"]) = filename.split(".")
            # checks if date is valide
            fileData["date"] = datetime.date(int(fileData["date"][0]
                                             + fileData["date"][1]
                                             + fileData["date"][2]
                                             + fileData["date"][3]),
                                             int(fileData["date"][4]
                                             + fileData["date"][5]),
                                             int(fileData["date"][6]
                                             + fileData["date"][7]))
            fileData["tags"] = fileData["tags"].split("_")
            fileData["place"] = str(fileData["date"])+"/"+fileData["filename"]
            if fileData["type"] == "pdf":
                return fileData
        except ValueError:
            raise ValueError("Filename {0} has not correct".format(filename)
                             + " format yyyymmdd.tag_tag_tag.pdf")

    def getList(self):
        # returns as generator every row of the newFilelist
        for file in self.newFileList:
            yield file

    def deleteItem(self, filename):
        pass


class placeFile(object):
    # Copies the File to the working dir, if nesassary creates dirs

    def __init__(self, filedata, config):
        # create dir if not existing
        self.dirName = config['managedDir']+str(filedata["date"])+"/"
        self.src = config['newFilesDir']+filedata["filename"]
        self.dest = self.dirName+filedata["filename"]
        self.mkDir()
        self.cpFile()
        self.rmFile()

    def mkDir(self):
        try:
            os.stat(self.dirName)
        except:
            os.makedirs(self.dirName)

    def cpFile(self):
        copyfile(self.src, self.dest)

    def rmFile(self):
        os.remove(self.src)


# DB Struktur
files_structur = '''
DROP TABLE IF EXISTS files;
CREATE TABLE files(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place TEXT NOT NULL,
    date DATE,
    type TEXT NOT NULL
    );'''

tags_structur = '''
DROP TABLE IF EXISTS tags;
CREATE TABLE tags(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
    );'''

tag_file_structur = '''
DROP TABLE IF EXISTS tag_file;
CREATE TABLE tag_file(
    files_id INTEGER,
    tags_id INTEGER,
    FOREIGN KEY(files_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY(tags_id) REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY(files_id, tags_id)
);
'''


class MyDB(object):
    def __init__(self, dbfile):
        self.connection = sqlite3.connect(dbfile,
                                          detect_types=sqlite3.PARSE_DECLTYPES
                                          | sqlite3.PARSE_COLNAMES)
        self.cursor = self.connection.cursor()

    def __del__(self):
        self.cursor.close()
        self.connection.close()

    def addFile(self, place, date, filetype):
        # insert int File Table
        query = "INSERT INTO files(place,date,type) Values(?,?,?)"
        values = (place, date, filetype)
        self.cursor.execute(query, values)
        self.connection.commit()
        return self.cursor.lastrowid

    def addItem(self, place, date, filetype, tags):
        # add the file
        fileId = self.addFile(place, date, filetype)

        # add tags
        tagIds = []
        for tag in tags:
            tagId = self.addTag(tag)
            if tagId:
                tagIds.append(tagId)

        # add relation
        for tagId in tagIds:
            self.addRelation(fileId, tagId)

    def addRelation(self, fileid, tagid):
        query = "INSERT INTO tag_file(files_id,tags_id) VALUES(?,?);"
        self.cursor.execute(query, (fileid, tagid))
        self.connection.commit()

    def addTag(self, name):
        # insert into TagTable
        tagId = self.getTagId(name)
        # if there is already a tag with this name return it
        if tagId:
            return tagId
        else:
            query = "INSERT INTO tags(name) Values(?)"
            self.cursor.execute(query, (name,))
            self.connection.commit()
            return self.cursor.lastrowid

    def buildStructure(self):
        self.cursor.executescript("{0}{1}{2}".format(files_structur,
                                                     tags_structur,
                                                     tag_file_structur)
                                  )
        self.connection.commit()

    def deleteFile(self, fid):
        self.cursor.execute("DELETE FROM files "
                            + "WHERE id=(?);", (str(fid),))
        self.connection.commit()

    def deleteTagconnectionsOfFile(self, fid):
        self.cursor.execute("DELETE FROM tag_file "
                            + "WHERE files_id=(?);", (str(fid),))
        self.connection.commit()

    def deleteTag(self, tid):
        self.cursor.execute("DELETE FROM tags "
                            + "WHERE id=(?);", (str(tid),))
        self.connection.commit()

    def getTag(self, tid):
        self.cursor.execute("SELECT name FROM tags "
                            + "WHERE id = (?);", (str(tid),))
        tag = self.cursor.fetchone()
        return tag[0] if tag else None

    def getTagId(self, name):
        self.cursor.execute("SELECT id FROM tags "
                            + "WHERE name LIKE (?);", ("%"+name+"%",))
        tagId = self.cursor.fetchone()
        return tagId[0] if tagId else None

    def getTagsOfFile(self, fid):
        self.cursor.execute("SELECT tags_id FROM tag_file "
                            + "WHERE files_id = (?);", (str(fid),))
        return(self.cursor.fetchall())

    def getTagList(self):
        self.cursor.execute("SELECT name FROM tags ORDER BY name;")
        return self.cursor.fetchall()

    def getTagConnectionCount(self, tag):
        self.cursor.execute("SELECT COUNT(files_id) FROM tag_file "
                            + "WHERE tags_id = (?);", (str(tag),))
        count = self.cursor.fetchone()
        return count[0] if count else None

    def getFileId(self, place):
        self.cursor.execute("SELECT id FROM files "
                            + "WHERE place = (?);", (place,))
        file_id = self.cursor.fetchone()
        return file_id[0] if file_id else None

    def getFilelist(self):
        self.cursor.execute("SELECT place FROM files Order BY place;")
        return self.cursor.fetchall()

    def getFilelistByTag(self, tags):
        tag_ids = []
        for tag in tags:
            tag_id = self.getTagId(tag)
            if tag_id:
                tag_ids.append(tag_id)
        if tag_ids:
            query = ("SELECT files.place "
                     + "FROM files "
                     + "WHERE id IN (")

            for tag_id in enumerate(tag_ids):
                if tag_id[0] > 0:
                    query += "INTERSECT "
                query += ("SELECT files_id FROM tag_file "
                          + "WHERE tags_id=(?) ")

            query += ") ORDER BY files.place;"
            self.cursor.execute(query, (tag_ids))
            return self.cursor.fetchall()


def main():

    parser = argparse.ArgumentParser(description="dms for python",
                                     prog="PyDMS.py")
    parser.add_argument("-c", "--cleanup", action="store_true",
                        help="cleaning up the db", default=False)
    parser.add_argument("-r", "--refresh", action="store_true",
                        help="searches for new Files in the DMS-Directory",
                        default=False)
    parser.add_argument("-v", "--verbose", action="store_true",
                        default=False)
    parser.add_argument("-s", "--search", action="store",
                        help="tag or a list of tags to search for",
                        nargs='+')
    parser.add_argument('-t', "--tags", action="store_true",
                        help="get a list of available tags")
    parser.add_argument('-f', "--files", action="store_true",
                        help="get a list of available files")
    parser.add_argument("--flushdb", action="store_true",
                        help="hope you know what you are doing", default=False)
    parser.add_argument('--version', action='version', version='0.2a')
    arguments = parser.parse_args()

    # Load the config
    if arguments.refresh:
        refresh(arguments.verbose)

    elif arguments.flushdb:
        db = MyDB(config['dbFile'])
        db.buildStructure()

    elif arguments.files:
        list_files()

    elif arguments.cleanup:
        cleanup()

    elif arguments.search:
        search(arguments.search, arguments.verbose)

    elif arguments.tags:
        list_tags()

    else:
        parser.print_help()

    return(0)


def list_files():
    # get a list of available files
    db = MyDB(config["dbFile"])
    filelist = db.getFilelist()
    for file in filelist:
        print(config['managedDir']+file)


def cleanup():
    '''
    cleaning up the db from dead file links
    getting file list
    check if file don't exist
        delete file
    check if tags of deleted file are now dead tags
    cleaning up the db from dead tags

    searching for new files
    '''
    db = MyDB(config["dbFile"])
    filelist = db.getFilelist()
    for entry in filelist:
        if not os.path.isfile(config["managedDir"]+entry[0]):
            # get file id
            fid = db.getFileId(entry[0])

            # get tags
            tags = db.getTagsOfFile(fid)

            # delete file
            db.deleteFile(fid)
            print('File ' + entry[0] + ' deleted!')

            # delete tag file conection
            db.deleteTagconnectionsOfFile(fid)
            print('Tagconnections deleted!')

            # if no entry with the tag delete tag
            for tag in tags:
                if not db.getTagConnectionCount(tag[0]):
                    tagname = db.getTag(tag[0])
                    db.deleteTag(tag[0])
                    print('Tag ' + tagname + " deleted!")


def refresh(verbose):
    # searching for new file in the new-directory write metadata into the db
    # a copy it into the directory-structur
    newFiles = newFile(config['newFilesDir'])

    for files in newFiles.getList():
        if verbose:
            print("Filename : {0}".format(files["filename"]))
            print("Date : {0}".format(files["date"]))
            print("Filetype : {0}".format(files["type"]))
            string = "Tags : "
            for tag in files["tags"]:
                string += "{0} ".format(tag)
            print("{0}".format(string))
            answer = input("Should I import?(y/n) ")
        else:
            answer = 'y'
        if answer in "yY":
            placeFile(files, config)
            db = MyDB(config['dbFile'])
            db.addItem(files["place"], files["date"], files["type"],
                       files["tags"])
            print("{0} added!\n".format(files["filename"]))


def search(searchstring, verbose):
    if verbose:
        print('Searchtags: ' + ' '.join(searchstring))
    db = MyDB(config['dbFile'])
    filelist = db.getFilelistByTag(searchstring)
    # print("\n".join(filelist))
    for file in filelist:
        print(config['managedDir']+file[0])


def list_tags():
    db = MyDB(config['dbFile'])
    tagList = db.getTagList()
    for tag in tagList:
        print(tag[0])

if __name__ == '__main__':
    main()
