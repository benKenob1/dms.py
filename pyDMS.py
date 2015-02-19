#!/usr/bin/env python3

import argparse
import sqlite3
import datetime
import os
from shutil import copyfile
'''
#########################################################
#config part for things that can only be confirated here
#########################################################
'''
config = {
    'managedDir': '/home/bheublein/Documents/klaut/DMS/',
    'newFilesDir': '/home/bheublein/Documents/klaut/DMS/new/',
    'dbTyp': 'SQLight',
    'dbFile': 'pyDMS.sql'
}


class newFile(object):
    '''
    Instances of this class are looking for new File
    makes a list of the files with all tags
    cleans the newsDir
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

tag_relation_structur = '''
DROP TABLE IF EXISTS tag_relation;
CREATE TABLE tag_relation(
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
        query = "INSERT INTO tag_relation(files_id,tags_id) VALUES(?,?);"
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
                                                     tag_relation_structur)
                                  )
        self.connection.commit()

    def getTagId(self, name):
        self.cursor.execute("SELECT id FROM tags WHERE name=(?);", (name,))
        tagId = self.cursor.fetchone()
        if tagId:
            return tagId[0]
        else:
            return None

    def getFilelist(self):
        self.cursor.execute("SELECT files_id,place FROM files;")

    def getFilelistByTag(self, tag):
        tagId = self.getTagId(tag)
        if tagId:
            self.cursor.execute("SELECT files.place "
                                + "FROM files "
                                + "JOIN  tag_relation "
                                + "ON files.id = tag_relation.files_id "
                                + "JOIN tags "
                                + "ON tags.id = tag_relation.tags_id "
                                + "WHERE tags.name LIKE ?"
                                + "ORDER BY files.place;", ("%"+tag+"%",))
            file = self.cursor.fetchone()
            while file:
                yield file[0]
                file = self.cursor.fetchone()


def main():

    parser = argparse.ArgumentParser(description="dms for python",
                                     prog="PyDMS.py")
    parser.add_argument("-c", "--cleanup", action="store_true",
                        help="cleaning up the db", default=False)
    parser.add_argument("-r", "--refresh", action="store_true",
                        help="searches for new Files in the DMS-Directory",
                        default=False)
    parser.add_argument("-s", "--search", action="store",
                        help="search for Files with your tags")
    parser.add_argument("--flushdb", action="store_true",
                        help="hope you know what you are doing", default=False)
    parser.add_argument('--version', action='version', version='0.1a')
    arguments = parser.parse_args()

    # Load the config
    if arguments.refresh:
        refresh()

    elif arguments.flushdb:
        db = MyDB(config['dbFile'])
        db.buildStructure()

    elif arguments.cleanup:
        cleanup()

    elif arguments.search:
        search(arguments.search)
    # elif options.bind:
    #    bind(config,options.bind)

    # else:
    #    parser.print_help()

    # verbose=options.verbose
    return(0)

'''
def bind(config, tag):
    #get file l ist by tag
    db=MyDB(config.dbFile)
    filelist=db.getFilelistByTag(tag)

    #write output
    pdf.bind(filelist,config.outputDir+tag+".pdf",config)
'''


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

    pass


def refresh():
    # searching for new file in the new-directory and asimlation it into the db
    # a copy it into the directory-structur
    newFiles = newFile(config['newFilesDir'])

    for files in newFiles.getList():
        print("Filename : {0}".format(files["filename"]))
        print("Date : {0}".format(files["date"]))
        print("Filetype : {0}".format(files["type"]))
        string = "Tags : "
        for tag in files["tags"]:
            string += "{0} ".format(tag)
        print("{0}".format(string))
        answer = input("Should I import?(y/n) ")
        if answer in "yY":
            placeFile(files, config)
            db = MyDB(config['dbFile'])
            db.addItem(files["place"], files["date"], files["type"],
                       files["tags"])
            print("File added!\n")


def search(searchstring):
    print(searchstring)
    db = MyDB(config['dbFile'])
    filelist = db.getFilelistByTag(searchstring)
    for file in filelist:
        print(file)

if __name__ == '__main__':
    main()
