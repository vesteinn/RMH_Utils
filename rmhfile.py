#!/usr/bin/env python3
"""
    Reynir: Natural language processing for Icelandic

     RMHFile

    Copyright (C) 2020 Miðeind ehf.

       This program is free software: you can redistribute it and/or modify
       it under the terms of the GNU General Public License as published by
       the Free Software Foundation, either version 3 of the License, or
       (at your option) any later version.
       This program is distributed in the hope that it will be useful,
       but WITHOUT ANY WARRANTY; without even the implied warranty of
       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
       GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see http://www.gnu.org/licenses/.

     Wrapper class for an xml resource file, as part of the RMH corpus.
"""


import xml.etree.cElementTree as ET
from collections import namedtuple
from pathlib import Path


URI = "http://www.tei-c.org/ns/1.0"
NAMESPACE = "{" + URI + "}"
ET.register_namespace("", URI)

Sentence = namedtuple("Sentence", "index tokens")
Token = namedtuple("Token", "text, lemma, tag")


class RMHFile:
    def __init__(self, path):
        self.path = path if isinstance(path, Path) else Path(path)
        self._root = None
        self._header = None
        self._source_desc = None
        self._idno = None

    @classmethod
    def fromstring(cls, data):
        inst = cls("")
        inst._root = ET.fromstring(data)
        inst.path = Path(inst.idno)
        inst.tsv_fname = inst.path.with_suffix(".tsv")
        inst.desc_fname = inst.path.with_suffix(".desc.xml")
        return inst

    @property
    def root(self):
        if self._root is not None:
            return self._root
        tree = ET.parse(self.path)
        self._root = tree.getroot()
        return self._root

    @property
    def header(self):
        if self._header is not None:
            return self._header
        self._header = self.root.find(f"{NAMESPACE}teiHeader")
        return self._header

    @property
    def idno(self):
        if self._idno is not None:
            return self._idno
        idno_elem = list(self.root.iter(f"{NAMESPACE}idno"))
        self._idno = idno_elem[0].text if idno_elem else None
        return self._idno

    @property
    def source_desc(self):
        if self._source_desc is not None:
            return self._source_desc
        self._source_desc = self.header.find(f"{NAMESPACE}sourceDesc")
        return self._source_desc

    @property
    def paragraphs(self):
        for pg in self.root.iterfind(f".//{NAMESPACE}div1/{NAMESPACE}p"):
            yield pg

    def __fspath__(self):
        return str(self.path)

    def is_on_disk(self, directory):
        tsv_path = (Path(directory) / self.idno).with_suffix(".tsv")
        desc_path = (Path(directory) / self.idno).with_suffix(".desc.xml")
        if tsv_path.is_file() and desc_path.is_file():
            return True
        return False

    @property
    def sentences(self):
        idno = self.idno
        for pg in self.paragraphs:
            pg_idx = pg.attrib.get("n")
            for sentence in pg.iterfind(f"{NAMESPACE}s"):
                sent_idx = sentence.attrib.get("n")
                tokens = []
                for item in sentence:
                    token = Token(
                        item.text,
                        item.attrib.get("lemma", item.text),
                        item.attrib.get("type", item.text),
                    )
                    tokens.append(token)
                sent_id = f"{idno}.{pg_idx}.{sent_idx}"
                yield Sentence(sent_id, tokens)

    def indexed_sentence_text(self):
        for sentence in self.sentences:
            yield sentence.index, " ".join([token.text for token in sentence.tokens])
