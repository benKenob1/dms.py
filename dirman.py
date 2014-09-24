#!/usr/bin/env python3

# Script: Dirman.py
# Description: File includes all functions and classe to interact with the
#              mother file system

# from math import isnan
import datetime
import os
from shutil import copyfile


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
        self.dirName = config.managedDir+str(filedata["date"])+"/"
        self.src = config.news+filedata["filename"]
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
