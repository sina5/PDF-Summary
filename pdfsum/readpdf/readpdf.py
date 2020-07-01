
# Programmer: Sina Fathi-Kazerooni
# Email: sina@sinafathi.com
# WWW: sinafathi.com 

import textract
import re
from spacy.lang.en import English

class ReadPDF(object):
    """This class opens a PDF file and converts it to plain text.

    Args:
        path (str): PDF file path.
    """
    def __init__(self, path):
        self.path = path
        self.text_len = 0
        
    def get_text(self):
        """Return the plain text of the document.

        Returns:
            str: Plain text of the document in binary or decoded format.
        """
        try:
            result = textract.process(self.path).\
                    decode().\
                    replace('\n', ' ').\
                    replace('\r','')
            self.text_len = len(result)
            return result
        except:
            return None
    
    def __len__(self):
        """Return the number of characters in the PDF text.

        Returns:
            int: Length of the input PDF.
        """
        return self.text_len

    def save_text(self, path='output/out.txt'):
        """Save PDF text to a file.

        Args:
            path (str, optional): Path to save text. 
            Defaults to 'output/out.txt'.
        """
        text = self.get_text()
        with open(path, 'wb') as f:
            f.write(text)

    def clean(self, text):
        """Remove repeated full stops from the document. 

        Args:
            text (str): Text to clean.

        Returns:
            str: Clean text.
        """
        text = re.sub(r'(\.\s+)+', ".", 
                    re.sub(r'\.+', ". ", text)) # remove redundant full stops
        return text
    
    def clean_sentences(self, text:str, pre_loaded_model=None, 
                min_len=40, max_len=400, return_sent_list=False):
        """Clean the sentences of the document by choosing the 
        ones with lengths between min_len and max_len. Sentences
        shorter than a certain length are usually not actual 
        sentences, but phrases or charcters ending in a full stop.

        Args:
            text (str): Text to clean.
            pre_loaded_model (str, optional): Spacy model to load for 
            identifying sentences. Defaults to None.
            min_len (int, optional): Minimum length for a phrase to be
            returned as a sentence. Defaults to 60.
            max_len (int, optional): Maximum length for a phrase to be 
            returned as a sentence. Defaults to 500.
            return_sent_list (bool, optional): Whether to return results 
            as a list or text data. Defaults to False.

        Returns:
            list or str: List of sentences or a str object containing 
            all the sentences.
        """
        if pre_loaded_model:
            nlp = pre_loaded_model
        else:
            nlp = English()
        nlp.add_pipe(nlp.create_pipe('sentencizer'))
        doc = nlp(text)
        clean = self.clean
        result = [clean(c.string.strip()) for c in doc.sents\
                     if max_len > len(clean(c.string.strip())) > min_len]
        if return_sent_list:
            return result
        else:
            return "".join(result)
  
      