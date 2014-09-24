#!/usr/bin/env python3

import argparse
from config import confMan
from db import MyDB
import dirman
# import pdf
'''
#########################################################
#config part for things that can only be confirated here
#########################################################
'''
configFile = "./config.yaml"


def main():

    # Load the config
    config = confMan(configFile)

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
        refresh(config)

    elif arguments.flushdb:
        db = MyDB(config.dbFile)
        db.buildStructure()

    elif arguments.cleanup:
        cleanup()

    elif arguments.search:
        search(arguments.search, config)
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


def refresh(config):
    # searching for new file in the new-directory and asimlation it into the db
    # a copy it into the directory-structur
    newFiles = dirman.newFile(config.news)

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
            dirman.placeFile(files, config)
            db = MyDB(config.dbFile)
            db.addItem(files["place"], files["date"], files["type"],
                       files["tags"])
            print("File added!\n")


def search(searchstring, config):
    print(searchstring)
    db = MyDB(config.dbFile)
    filelist = db.getFilelistByTag(searchstring)
    for file in filelist:
        print(file)

if __name__ == '__main__':
    main()
