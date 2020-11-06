from typing import List, Tuple, Optional

import nltk
import logging
from pedantic import pedantic_class

from src.exception.language_processing_errors import NoChunkFoundError, \
    MultipleChunksFoundError
from src.nlp.IChunker import IChunker


@pedantic_class
class Chunker(IChunker):
    """
    A class that contains logic to preprocess text and find chunks of text.
    """

    def __init__(self, chunk_grams: str = '',
                 tagged_words_bypass: Optional[
                     List[Tuple[str, str]]] = None) -> None:
        self.grammars = self.set_regex_grammars(grammars=chunk_grams)
        self.tagged_words_bypass = tagged_words_bypass

    def set_regex_grammars(self, grammars: str='') -> str:
        """
        A function containing all predefined chunk-grammars.
        (in later development they will put in a seperate
        file that is generated by a GUI-Tool.)
        """
        if grammars != '' and grammars is not None:
            return grammars
        else:
            # take those as default grammars
            return r"""
            VB_NN_TO_NN:    {<VB.?>+<NN.?><TO><NN.?>+}
            NN_VB_NN:       {<NN.?><VB.?><NN.?>}
            """

    def find_chunk(self, text: str) -> nltk.tree.Tree:
        return super().find_chunk(text=text)

    def preprocess(self, text: str) -> List[Tuple[str, str]]:
        # Sentence Tokenizing.
        # from 'long sentence1. long sentence' to
        # [long sentence1', 'long sentence2']
        sentences = nltk.sent_tokenize(text)

        # requirement - constraint: only one sentence is allowed.
        sentence = sentences[0]

        # Word Tokenizing
        # from ['long sentence1'] to ['long', 'sentence1']
        sentence = nltk.wordpunct_tokenize(sentence)

        # Lowercase Normalisation
        # from ["Long", "Sentence"] to ["long", "sentence"]
        # sentence = [word.lower() for word in sentence]

        # Optional: Stop word removal
        # # from [["long", "to", "bar"]] to [["long", "bar"]]
        # def stopword_removal(sentence):
        #     return [word for word in sentence if word not in stopwords]
        # sentences = [stopword_removal(sent) for sent in sentences]

        # POS Tagging
        tagged_sentence = nltk.pos_tag(sentence)

        # # Optional: Lemmatize   - might be useful for more advanced
        # # nlp in near future. So I leave it here.
        # # from [["longer", "bar"]] to [["long", "bar"]]
        # def lemmatize_sentence(sentence, lemmatizer):
        #     return [lemmatizer.lemmatize(word=word) for word in sentence]
        # lemmatizer = nltk.stem.WordNetLemmatizer()
        # sentences= [lemmatize_sentence(sent,lemmatizer) for sent in sentences]

        # sadly there are words, that a pos tagger always classifies wrong.
        # We correct them here.
        def _check_bypass(tuple_to_check: Tuple[str, str]) -> Tuple[str, str]:
            if self.tagged_words_bypass is not None:
                for bypass_tuple in self.tagged_words_bypass:
                    if tuple_to_check[0] == bypass_tuple[0]:
                        return tuple_to_check[0], bypass_tuple[1]
            return tuple_to_check

        for idx, tagged_word in enumerate(tagged_sentence):
            tagged_sentence[idx] = _check_bypass(tuple_to_check=tagged_word)

        return tagged_sentence
