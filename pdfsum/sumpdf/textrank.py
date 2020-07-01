
# Programmer: Sina Fathi-Kazerooni
# Email: sina@sinafathi.com
# WWW: sinafathi.com 
##############################################################################

import re
import pytextrank
import spacy
import pandas as pd
import numpy as np
from tqdm import tqdm
from math import sqrt
from operator import itemgetter
from spacy import displacy
from spacy.matcher import Matcher
from spacy.matcher import PhraseMatcher
from spacy.scorer import Scorer
from scispacy.abbreviation import AbbreviationDetector
from scispacy.umls_linking import UmlsEntityLinker
from scispacy.linking import EntityLinker
from scispacy.custom_sentence_segmenter import\
     combined_rule_sentence_segmenter
from scispacy.custom_tokenizer import\
     remove_new_lines, combined_rule_tokenizer

class TextSum(object):
    def __init__(self):
        self.nlp = None
        self.matcher= None
        self.matched_sents = []
        self.phrases_w_bacteria = None
        self.phrases_w_food = None
        self.phrases_w_pregnancy = None
        self.phrases_w_diseases = None
        self.sent_bounds = []
        self.unit_vector = []
        self.phrase_id = 0
        self.text_for_summary=""

    def load_dictionary(self, name='en_core_sci_lg'):
        """Load SciSpacy dictionary

        Args:
            name (str, optional): Name of the vocabulary. 
                Defaults to 'en_core_sci_lg'.

        Returns:
            spacy.lang: Spacy vocabulary 
        """
        print('\n\nLoading dictionary {}...'.format(name))
        self.nlp = spacy.load(name)
        self.matcher = Matcher(self.nlp.vocab)
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        print('Dictionary loaded successfully.')
        return self.nlp
        
    def _get_lemmas(self, doc):
        """Get lemmatization results for document.

        Args:
            doc (spacy.doc): Parsed spacy document.

        Returns:
            list: list of all document lemmatized tokens.
        """
        result = []
        for token in doc:
            if (token.is_alpha and 
            not (token.is_space or token.is_punct or 
                 token.is_stop or token.like_num)):
                if len(str(token.lemma_))>1:
                    result.append(token.lemma_)
        return result

    def get_text(self, text_data, remove_references=True):
        """Tokenize and lemmatize the input text.

        Args:
            text_data (str): Document text body
            remove_references (bool, optional): Remove references from 
            document body. Defaults to True.

        Returns:
            spacy.doc: Processed text by Spacy.
        """
        if not self.nlp:
            print('Vocabulary is not loaded.')
            return None
        print('\n\nProcessing the document...')
        if remove_references: # Remove article references
            splits = re.split("references", text_data, flags=re.IGNORECASE)
            if splits:
                if (len(splits) > 0):
                    text_data =  ' '.join(splits[:-1])
            # remove numbers in square bracket:
            text_data=re.sub("[\[].*?[\]]", "", text_data)
        doc = self.nlp(text_data) # Process document with Spacy
        print('Finished processing the document.')
        return doc
        

    def add_pipe(self, pipe):
        """Add Spacy pipes

        Args:
            pipe (str): pipe name
        """
        print('Loading Spacy pipe: {}'.format(pipe))
        pipe = pipe.lower()
        if pipe == 'abbreviation': # Abbreviation extraction
            abbreviation_pipe = AbbreviationDetector(self.nlp)
            self.nlp.add_pipe(abbreviation_pipe)
        elif pipe == 'entitylinker': # Entity linker
            linker = UmlsEntityLinker(resolve_abbreviations=True)
            self.nlp.add_pipe(linker)
        elif pipe == 'segmenter': # Rule Segmenter
            self.nlp.add_pipe(combined_rule_sentence_segmenter, first=True)
        elif pipe == 'tokenizer': # Tokenizer
            self.nlp.tokenizer = combined_rule_tokenizer(self.nlp)
        elif pipe == 'textrank': # Textrank
            tr = pytextrank.TextRank()
            self.nlp.add_pipe(tr.PipelineComponent, name='textrank', 
                            last=True)
        print('Pipe loaded.')


    def get_text_rank_summary(self, doc, limit_sentences=20, verbose = True):
        """Get extractive summary from textrank.

        Args:
            doc (spacy.doc): Parsed spacy document.
            limit_sentences (int, optional): Length of summary. 
                Defaults to 20.
            verbose (bool, optional): Whether or not print results. 
                Defaults to True.
        
        Returns:
            list: Summary
        """
        result =  doc._.textrank.summary(limit_sentences=limit_sentences)
        res = ''
        
        for sent in result:
            res+='{} '.format(sent)
            if verbose:
                print(sent)
        return res
    
    def create_patterns(self, unique_keys, phrase_pattern = False):
        pattern = []
        if phrase_pattern:
            for item in unique_keys:
                pattern.append(self.nlp.make_doc(item.lower()))
        else:
            for item in unique_keys:
                pattern.append([{"LOWER": item.lower()}])
        return pattern


    def collect_sents(self, matcher, doc, i, matches):
        """This function collects sentences matched with phrases or tokens.
        This function is originally from Spacy website.

        Args:
            matcher (apacy.matcher): Spacy matcher instance.
            doc (spacy.doc): Spacy document.
            i (int): Iteration index.
            matches (list): List of matches.

        Returns:
            list: List of matches.
        """
        matched_sents = self.matched_sents
        match_id, start, end = matches[i]
        span = doc[start:end]  # Matched span
        sent = span.sent  # Sentence containing matched span
        match_ents = [{
            "start": span.start_char - sent.start_char,
            "end": span.end_char - sent.start_char,
            "label": "MATCH",
        }]
        matched_sents.append({"text": sent.text, "ents": match_ents})
        self.matched_sents = matched_sents
        return matched_sents
    
    def match_token_patterns(self, doc, pattern=[]):
        """Match a list of token patterns with document body.

        Args:
            doc (spacy.doc): Spacy document.
            pattern (list, optional): List of patterns. Defaults to [].

        Returns:
            list: List of matched phrases.
        """
        self.matched_sents = []
        self.matcher.add("PDFTokens", 
                        self.collect_sents, 
                        *pattern)  # add pattern
        matches = self.matcher(doc)
        return matches
    
    def match_phrase_patterns(self, doc, pattern=[]):
        """Match a list of phrases patterns with document body.

        Args:
            doc (spacy.doc): Spacy document.
            pattern (list, optional): List of patterns. Defaults to [].

        Returns:
            list: List of matched phrases.
        """
        self.matched_sents = []
        self.phrase_matcher.add("PDFPhrases", 
                            self.collect_sents, 
                            *pattern)  # add pattern
        matches = self.phrase_matcher(doc)
        return matches

    def get_matched_sents(self):
        """A list of matched sentences from pattern matching.

        Returns:
            list: List of matched sentences.
        """
        return self.matched_sents