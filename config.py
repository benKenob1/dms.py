#!/usr/bin/env python3
## @package config
#
#  config.py
#  script inlcudes the class to load and save the config

## nessessary for understanding the file
import yaml

## The class to load data from the config
# @param object Reference to the object itself
class confMan(object):
    ## the constructor
    # @param self Reference to the object itself
    # @param configFile a String including the path to the  Yaml-Configfile


    def __init__(self,configFile):

        #Opens the mainconfig-File
        yamlFile=open("%s"%configFile,"r")

        #Loads the Data from the file
        data=yaml.load(yamlFile)

        #Save the Data in local variables
        self.managedDir = data["managedDir"]
        self.news = data["managedDir"]+data["newFiles"]
        self.dbTyp = data["dbTyp"]
        self.dbFile = data["dbFile"]
        self.outputDir = data["outputDir"]

        #Close the YamlFile
        yamlFile.close()


