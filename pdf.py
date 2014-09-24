#!/usr/bin/env python3
'''
from PyPDF2 import PdfFileWriter, PdfFileReader

def bind(filelist,output,config):
    #combines als files of files list to a new file output
    pdfwrite = PdfFileWriter()
    for item in filelist:
        input=PdfFileReader(file(config.managedDir+item,"rb"))
        for page in range(input.getNumPages()):
            pdfwrite.addPage(input.getPage(page))

    outputfile = file(config.managedDir+output,"wb")
    pdfwrite.write(outputfile)
    outputfile.close
'''
