#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime
from flask import current_app
from textwrap import fill
from itertools import product
from string import ascii_uppercase
import re
import json

from exportsrv.formatter.toLaTex import encode_laTex, encode_laTex_author

# This class accepts JSON object created by Solr and reformats it
# for the BibTex Export formats we are supporting
# 1- To get Reference BibTex without Abstract use
#    referenceXML = BibTexFormat(jsonFromSolr).getReferenceBibTex()
# 2- To get Reference BibTex with Abstract use
#    referenceXML = BibTexFormat(jsonFromSolr).getReferenceBibTex(True)

class BibTexFormat:

    REGEX_AUTHOR = re.compile(r'([A-Z])\w*')
    REGEX_PUB_RAW = dict([
        (re.compile(r"(\;?\s*\<ALTJOURNAL\>.*\</ALTJOURNAL\>\s*)"), r""),  # remove these
        (re.compile(r"(\;?\s*\<CONF_METADATA\>.*\<CONF_METADATA\>\s*)"), r""),
        (re.compile(r"(?:\<ISBN\>)(.*)(?:\</ISBN\>)"), r"\1"),  # get value inside the tag for these
        (re.compile(r"(?:\<NUMPAGES\>)(.*)(?:</NUMPAGES>)"), r"\1"),
    ])

    status = -1
    from_solr = {}

    def __init__(self, from_solr):
        self.from_solr = from_solr
        if (self.from_solr.get('responseHeader')):
            self.status = self.from_solr['responseHeader'].get('status', self.status)


    def get_status(self):
        return self.status


    def get_num_docs(self):
        if (self.status == 0):
            if (self.from_solr.get('response')):
                return self.from_solr['response'].get('numFound', 0)
        return 0


    def __get_doc_type(self, solr_type):
        """
        from solr to BibTex document type

        :param solr_type:
        :return:
        """
        fields = {'article':'@ARTICLE', 'circular':'@ARTICLE', 'newsletter':'@ARTICLE',
                  'eprint':'@ARTICLE', 'catalog':'@ARTICLE',
                  'book':'@BOOK', 
                  'inbook':'@INBOOK',
                  'proceedings':'@PROCEEDINGS', 
                  'inproceedings':'@INPROCEEDINGS', 'abstract':'@INPROCEEDINGS',
                  'misc':'@MISC', 'software':'@MISC','proposal':'@MISC', 'pressrelease':'@MISC',
                  'talk':'@INPROCEEDINGS',
                  'phdthesis':'@PHDTHESIS','mastersthesis':'@MASTERSTHESIS',
                  'techreport':'@TECHREPORT', 'intechreport':'@TECHREPORT'}
        return fields.get(solr_type, '')


    def __format_date(self, solr_date):
        # solr_date has the format 2017-12-01T00:00:00Z
        date_time = datetime.strptime(solr_date, '%Y-%m-%dT%H:%M:%SZ')
        return date_time.strftime('%b')


    def __format_line_wrapped(self, left, right, format_style):
        wrapped = fill(right, width=72, subsequent_indent=' ' * 8)
        return format_style.format(left, wrapped)


    def __get_fields(self, a_doc):
        """
        exported fields for various document types

        :param a_doc:
        :return:
        """
        doc_type_bibtex = self.__get_doc_type(a_doc.get('doctype', ''))
        if (doc_type_bibtex == '@ARTICLE'):
            fields = [('author', 'author'), ('title', 'title'), ('pub', 'journal'),
                      ('keyword', 'keywords'), ('year', 'year'), ('month', 'month'),
                      ('volume', 'volume'), ('eid', 'eid'), ('page', 'pages'),
                      ('abstract', 'abstract'), ('doi', 'doi'), ('bibcode', 'adsurl'),
                      ('adsnotes', 'adsnote')]
        elif (doc_type_bibtex == '@BOOK'):
            fields = [('author', 'author'), ('title', 'title'), ('pub_raw', 'booktitle'),
                      ('year', 'year'), ('bibcode', 'adsurl'), ('adsnotes', 'adsnote')]
        elif (doc_type_bibtex == '@INBOOK'):
            fields = [('author', 'author'), ('title', 'title'), ('keyword', 'keywords'),
                      ('pub_raw', 'booktitle'), ('year', 'year'), ('editor', 'editor'),
                      ('page', 'pages'), ('abstract', 'abstract'), ('doi', 'doi'),
                      ('bibcode', 'adsurl'), ('adsnotes', 'adsnote')]
        elif (doc_type_bibtex == '@PROCEEDINGS'):
            fields = [('title', 'title'), ('keyword', 'keywords'), ('pub_raw', 'booktitle'),
                      ('year', 'year'), ('editor', 'editor'), ('series', 'series'),
                      ('volume', 'volume'), ('month', 'month'), ('doi', 'doi'),
                      ('abstract', 'abstract'), ('bibcode', 'adsurl'), ('adsnotes', 'adsnote')]
        elif (doc_type_bibtex == '@INPROCEEDINGS'):
            fields = [('author', 'author'), ('title', 'title'), ('keyword', 'keywords'),
                      ('pub_raw', 'booktitle'), ('year', 'year'), ('editor', 'editor'),
                      ('series', 'series'), ('volume', 'volume'), ('month', 'month'),
                      ('eid', 'eid'), ('page', 'pages'), ('abstract', 'abstract'),
                      ('doi', 'doi'), ('bibcode', 'adsurl'), ('adsnotes', 'adsnote')]
        elif (doc_type_bibtex == '@MISC'):
            fields = [('author', 'author'), ('title', 'title'), ('keyword', 'keywords'),
                      ('pub', 'howpublished'), ('year', 'year'), ('month', 'month'),
                      ('eid', 'eprint'), ('bibcode', 'adsurl'), ('adsnotes', 'adsnote')]
        elif (doc_type_bibtex == '@PHDTHESIS') or (doc_type_bibtex == '@MASTERSTHESIS'):
            fields = [('author', 'author'), ('title', 'title'), ('keyword', 'keywords'),
                      ('aff', 'school'), ('year', 'year'), ('month', 'month'),
                      ('bibcode', 'adsurl'),('adsnotes', 'adsnote')]
        elif (doc_type_bibtex == '@TECHREPORT'):
            fields = [('author', 'author'), ('title', 'title'), ('pub', 'journal'),
                      ('keyword', 'keywords'), ('pub_raw', 'booktitle'), ('year', 'year'),
                      ('editor', 'editor'), ('month', 'month'), ('volume', 'volume'),
                      ('bibcode', 'adsurl'), ('adsnotes', 'adsnote')]
        else:
            fields = []
        return OrderedDict(fields)

    def __get_author_list(self, a_doc):
        """
        format authors

        :param a_doc:
        :return:
        """
        if 'author' not in a_doc:
            return ''
        and_str = ' and '
        author_list = ''
        for author in a_doc['author']:
            author_parts = author.split(', ')
            author_list += '{' + author_parts[0] + '}'
            if (len(author_parts) >= 2):
                author_list += ", " +  '. '.join(self.REGEX_AUTHOR.findall(author_parts[1])) + '.' + and_str
        if (author_list.endswith(and_str)):
            author_list = author_list[:-len(and_str)]
        return encode_laTex_author(author_list)


    def __get_affiliation_list(self, a_doc):
        """
        format affiliation

        :param a_doc:
        :return:
        """
        if ('aff') not in a_doc:
            return ''
        counter = [''.join(i) for i in product(ascii_uppercase, repeat=2)]
        separator = ', '
        affiliation_list = ''
        addCount = not (a_doc.get('doctype', '') in ['phdthesis'])
        for affiliation, i in zip(a_doc['aff'], range(len(a_doc['aff']))):
            if (addCount):
                affiliation_list += counter[i] + '(' + affiliation + ')' + separator
            else:
                affiliation_list += affiliation + separator
        # do not need the last separator
        if (len(affiliation_list) > len(separator)):
            affiliation_list = affiliation_list[:-len(separator)]
        return encode_laTex(affiliation_list)


    def __add_keywords(self, a_doc):
        """
        format keywords

        :param a_doc:
        :return:
        """
        if 'keyword' not in a_doc:
            return ''
        return encode_laTex(', '.join(a_doc.get('keyword', '')))

    
    def __add_clean_pub_raw(self, a_doc):
        """
        parse pub_raw and eliminate tags
        
        :param a_doc: 
        :return: 
        """
        pub_raw = ''.join(a_doc.get('pub_raw', ''))
        # proceed only if necessary
        if ('<' in pub_raw) and ('>' in pub_raw):
            for key in self.REGEX_PUB_RAW:
                pub_raw = key.sub(self.REGEX_PUB_RAW[key], pub_raw)
        return pub_raw


    def __add_in(self, field, value, output_format):
        """
        add the value into the return structure, only if a value was defined in Solr
        
        :param field: 
        :param value: 
        :param output_format: 
        :return: 
        """
        if (((isinstance(value, unicode)) or (isinstance(value, str))) and (len(value) > 0)) or \
           ((isinstance(value, int)) and (value is not None)):
            return output_format.format(field, value) + ',\n'
        return ''

    
    def __add_in_wrapped(self, field, value, output_format):
        """
        add the value into the return structure, only if a value was defined in Solr
        
        :param field: 
        :param value: 
        :param output_format: 
        :return: 
        """
        if (len(value) > 0):
            return self.__format_line_wrapped(field, value, output_format) + ',\n'
        return ''

    
    def __get_doc(self, index, include_abs):
        """
        for each document from Solr, get the fields, and format them accordingly
        
        :param index: 
        :param include_abs: 
        :return: 
        """
        format_style_bracket_quotes = u'{0:>12} = "{{{1}}}"'
        format_style_bracket = u'{0:>12} = {{{1}}}'
        format_style = u'{0:>12} = {1}'

        a_doc = self.from_solr['response'].get('docs')[index]
        text = self.__get_doc_type(a_doc.get('doctype', '')) + '{' + a_doc.get('bibcode', '')  + ',\n'

        fields = self.__get_fields(a_doc)
        for field in fields:
            if (field == 'author'):
                text += self.__add_in_wrapped(fields[field], self.__get_author_list(a_doc), format_style_bracket)
            elif (field == 'title'):
                text += self.__add_in_wrapped(fields[field], encode_laTex(''.join(a_doc.get(field, ''))), format_style_bracket_quotes)
            elif (field == 'aff'):
                text += self.__add_in_wrapped(fields[field], self.__get_affiliation_list(a_doc), format_style_bracket)
            elif (field == 'pub_raw'):
                text += self.__add_in_wrapped(fields[field], self.__add_clean_pub_raw(a_doc), format_style_bracket)
            elif (field == 'pub') or (field == 'doi'):
                text += self.__add_in(fields[field], ''.join(a_doc.get(field, '')), format_style_bracket)
            elif (field == 'keyword'):
                text += self.__add_in_wrapped(fields[field], self.__add_keywords(a_doc), format_style_bracket)
            elif (field == 'year') or (field == 'volume'):
                text += self.__add_in(fields[field], int(a_doc.get(field, '')) if a_doc.get(field, '') else None, format_style)
            elif (field == 'month'):
                text += self.__add_in(fields[field], self.__format_date(a_doc.get('date', '')), format_style)
            elif (field == 'abstract') and (include_abs):
                text += self.__add_in_wrapped(fields[field], encode_laTex(a_doc.get(field, '')), format_style_bracket_quotes)
            elif (field == 'eid'):
                text += self.__add_in(fields[field], a_doc.get(field, ''), format_style_bracket)
            elif (field == 'page'):
                text += self.__add_in(fields[field], ''.join(a_doc.get(field, '')), format_style_bracket)
            elif (field == 'bibcode'):
                text += self.__add_in(fields[field], current_app.config['EXPORT_SERVICE_BBB_PATH'] + '/' + a_doc.get(field, ''), format_style_bracket)
            elif (field == 'adsnotes'):
                text += self.__add_in(fields[field], current_app.config['EXPORT_SERVICE_ADS_NOTES'], format_style_bracket)
        # remove the last comma,
        text = text[:-len(',\n')] + '\n'

        return text + '}\n\n'


    def get(self, include_abs=False):
        """
        
        :param include_abs: 
        :return: 
        """
        num_docs = 0
        ref_BibTex = []
        if (self.status == 0):
            num_docs = self.get_num_docs()
            for index in range(num_docs):
                ref_BibTex.append(self.__get_doc(index, include_abs))
        result_dict = {}
        result_dict['msg'] = 'Retrieved {} abstracts, starting with number 1.'.format(num_docs)
        result_dict['export'] = ''.join(record for record in ref_BibTex)
        return json.dumps(result_dict)
