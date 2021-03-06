import copy

import pytest

from src.exception.token_state_errors import MissingAttributeInTokenError
from src.models.running_token import RunningToken
from src.models.token import Token
from src.models.token_state_modification import \
    TokenStateModification


class TestToken:

    def test_new_attribute(self, empty_token):
        v1 = 'v1'
        empty_token.k = v1
        r = empty_token.k
        assert r == v1

    def test_new_attribute2(self, empty_token):
        v1 = 'v1'
        v2 = 'v2',
        empty_token.k1 =v1
        empty_token.k2 = v2
        r1 = empty_token.k1
        r2 = empty_token.k2
        assert v1 == r1
        assert v2 == r2

    def test_new_attribute3(self, empty_token):
        # trying to override existing attribute with
        # a new value - should work
        v1 = 'v1'
        v2 = 'v2'
        empty_token.k1 = v1
        r1 = empty_token.k1
        empty_token.k1 = v2
        r2 = empty_token.k1
        assert v1 == r1 != r2

    def test_new_attribute_none(self, empty_token):
        v1 = None
        empty_token.k1 = v1
        r = empty_token.k1
        assert r is None

    def test_override_value(self, empty_running_token):
        v1 = 'v1'
        empty_running_token.k1 = v1
        def m(t): t.k1 = 'v2'
        tsm = TokenStateModification(m)

        tsm.change_token(token=empty_running_token)
        assert empty_running_token.k1 == 'v2'

    def test_change_value_not_present(self, empty_running_token):
        # changing value of non existing key
        with pytest.raises(MissingAttributeInTokenError):
            def m(t): t.k1 = 'v1'
            tsm = TokenStateModification(m)
            tsm.change_token(token=empty_running_token)

    def test_get_nonexisting_key(self, empty_token):
        with pytest.raises(MissingAttributeInTokenError):
            empty_token.k42

    def test_not_contains_syntax(self, empty_token):
        assert 'k42' not in empty_token

    def test_contains_syntax(self, example_token):
        assert 'k1' in example_token

    def test_equal_reference(self, example_token):
        token_copy = example_token
        assert token_copy == example_token

    def test_equal_deepcopy_token(self, example_token):
        with pytest.raises(NotImplementedError):
            copy.deepcopy(example_token)

    def test_equal_copy_token(self, example_token):
        with pytest.raises(NotImplementedError):
            copy.copy(example_token)

    def test_equal_new_token(self, example_token):
        # same keys and values from examples token above
        attributes = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'}
        token2 = Token(attributes=attributes)
        assert token2 == example_token

    def test_dict_copy(self, example_token):
        attributes = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'}
        token = Token(attributes=attributes)
        assert token == token.copy()

    def test_equal_one_empty(self, empty_token, example_token):
        assert empty_token != example_token

    def test_equal_additional_key(self):
        attributes1 = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'}
        attributes2 = {'k1': 'v1', 'k2': 'v2'}
        token1 = Token(attributes=attributes1)
        token2 = Token(attributes=attributes2)
        assert token1 != token2

    def test_equal_different_value(self, example_running_token):
        token2 = RunningToken.from_token(token=example_running_token)
        def m(t): t.k1 = 'v42'
        tsm = TokenStateModification(m)
        tsm.change_token(token=token2)
        assert token2 != example_running_token

    def test_equals_different_type_combinations(self):
        # comparing Token, RunningToken with Token and RunningToken
        # to check if there are type erros in equal-function
        attributes = {'a': 1}
        token = Token(attributes=attributes)
        token2 = Token(attributes=attributes)
        running_token = RunningToken(attributes=attributes)
        running_token2 = RunningToken(attributes=attributes)

        assert token == token2
        assert running_token == running_token2
        assert token == running_token
        assert running_token == token

    def test_space_in_token_attribute(self):
        with pytest.raises(SyntaxError):
            Token(attributes={'attr attr': 43})

    def test_increment(self):
        key = 'k1'
        attributes = {key: 0}
        token = RunningToken(attributes=attributes)
        def m(t): t.k1 += 1
        tsm = TokenStateModification(m)
        tsm.change_token(token=token)
        assert token[key] == 1

    def test_from_token(self):
        token = Token(attributes={'a':0})
        running_token = RunningToken.from_token(token=token)
        assert token == running_token

        # test if changes on one are not reflected to other token
        running_token.a = 1
        assert running_token != token

        token.a = 2
        assert running_token != token
