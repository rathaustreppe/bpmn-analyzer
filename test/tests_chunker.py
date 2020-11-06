from typing import List, Tuple

import pytest

from src.exception.language_processing_errors import NoChunkFoundError, \
    MultipleChunksFoundError
from src.nlp.chunker import Chunker
from src.nlp.default_chunker import DefaultChunker


class TestChunker:
    @staticmethod
    def tuple_to_str(tuple_list: List[Tuple[str, str]]):
        text = []
        for elem in tuple_list:
            text.append(elem[0])
        return ' '.join(text)

    def test_chunker_simple_noun(self, nn_chunker, nn_word):
        text = self.tuple_to_str(tuple_list=nn_word)
        chunk = nn_chunker.find_chunk(text=text)
        assert len(chunk.leaves()) == 1
        assert chunk.leaves() == nn_word
        assert chunk.label() == 'NN_Chunk'

    def test_chunker_no_chunks(self, nn_word):
        # no found chunks leads to an error
        text = self.tuple_to_str(tuple_list=nn_word)
        chunker = Chunker(chunk_grams='')
        with pytest.raises(NoChunkFoundError):
            chunker.find_chunk(text=text)

    def test_chunker_double_chunk(self, nn_chunker, nn_word):
        # two chunks per sentence is not allowed
        text = self.tuple_to_str(tuple_list=nn_word) + " " \
               + self.tuple_to_str(tuple_list=nn_word)
        with pytest.raises(MultipleChunksFoundError):
            nn_chunker.find_chunk(text=text)

    def test_chunker_complex_chunk(self, nn_vb_nn_chunker, nn_vb_nn_sentence):
        text = self.tuple_to_str(tuple_list=nn_vb_nn_sentence)
        chunk = nn_vb_nn_chunker.find_chunk(text=text)
        assert len(chunk.leaves()) == len(nn_vb_nn_sentence)
        for idx, leave in enumerate(chunk.leaves()):
            assert leave == nn_vb_nn_sentence[idx]
        assert chunk.label() == 'NN_VB_NN'

    def test_chunker_longer_sentence(self, nn_chunker, xx_nn_xx_sentence):
        text = self.tuple_to_str(tuple_list=xx_nn_xx_sentence)
        chunk = nn_chunker.find_chunk(text=text)
        assert len(chunk.leaves()) == 1
        assert chunk.leaves()[0] == xx_nn_xx_sentence[1]
        assert chunk.label() == 'NN_Chunk'

    def test_default_chunker_word_preprocessing(self):
        text = 'green'
        chunker = DefaultChunker()
        processed_text = chunker.preprocess(text=text)
        assert len(processed_text) == 1
        assert processed_text[0] == (text, 'NN') #default tagger tags everything as noun

    def test_default_chunker_text_preprocessing(self):
        text = 'i like trains'
        chunker = DefaultChunker()
        processed_text = chunker.preprocess(text=text)
        assert len(processed_text) == 1
        assert processed_text[0] == (text, 'NN')

    def test_default_chunker_one_word_chunking(self):
        text = 'green'
        chunker = DefaultChunker()
        chunk = chunker.find_chunk(text=text)
        assert len(chunk.leaves()) == 1
        assert chunk.leaves()[0] == (text, 'NN')

    def test_default_chunker_sentence_chunking(self):
        text = 'i like trains'
        chunker = DefaultChunker()
        chunk = chunker.find_chunk(text=text)
        assert len(chunk.leaves()) == 1
        assert chunk.leaves()[0] == (text, 'NN')

    def test_default_chunker_multi_sentence_chunking(self):
        text = 'I like 99.9 trains. What about you?'
        chunker = DefaultChunker()
        chunk = chunker.find_chunk(text=text)
        assert len(chunk.leaves()) == 1
        assert chunk.leaves()[0] == (text, 'NN')