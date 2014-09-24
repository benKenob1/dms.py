#!/usr/bin/env python3


# DB Struktur
files_structur = '''
CREATE TABLE files(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place TEXT NOT NULL,
    date DATE,
    type TEXT NOT NULL
    );'''

tags_structur = '''
CREATE TABLE tags(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
    );'''

tag_relation_structur = '''
CREATE TABLE tag_relation(
    files_id INTEGER,
    tags_id INTEGER,
    FOREIGN KEY(files_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY(tags_id) REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY(files_id, tags_id)
);
'''
import sqlite3


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
        self.cursor.executescript("""
            DROP TABLE IF EXISTS files;
            DROP TABLE IF EXISTS tags;
            DROP TABLE IF EXISTS tag_relation;
            CREATE TABLE files(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                place TEXT NOT NULL,
                date DATE,
                type TEXT NOT NULL
            );

            CREATE TABLE tags(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );

            CREATE TABLE tag_relation(
                files_id INTEGER,
                tags_id INTEGER,
                FOREIGN KEY(files_id) REFERENCES files(id) ON DELETE CASCADE,
                FOREIGN KEY(tags_id) REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY(files_id, tags_id)
            );
           """)
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
