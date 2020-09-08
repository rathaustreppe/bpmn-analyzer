import pytest

from src.models.token import Token
from src.models.token_state_condition import Operators, \
    TokenStateCondition


class TestTokenStateCondition:
    @pytest.fixture(autouse=True)
    def empty_rule(self):
        self.empty_rule = \
            TokenStateCondition(
                tok_attribute='',
                operator=Operators.EQUALS,
                tok_value=None)

    @pytest.fixture(autouse=True)
    def example_rule(self):
        self.example_rule = TokenStateCondition(
            tok_attribute='k1',
            operator=Operators.EQUALS,
            tok_value='v1')

    @pytest.fixture(autouse=True)
    def example_token(self):
        attributes = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'}
        self.example_token = Token(attributes=attributes)

    def test_operator_not_implemented(self):
        # even with enums, you never know...
        with pytest.raises(Exception):
            TokenStateCondition(tok_attribute='',
                           operator=Operators.XYZ,
                           tok_value=None)

    def test_empty_token_attribute(self, empty_token):
        # empty token attribute raises error
        with pytest.raises(KeyError):
            self.empty_rule.check_condition(
                token=empty_token)

    def test_nonexisting_token_attribute_in_rule(self, empty_token):
        # apply token_attribute in rule that does not
        # exist in token
        with pytest.raises(KeyError):
            self.example_rule.check_condition(
                token=empty_token)

    def test_rule_with_none_value(self):
        # rule checks for none-value
        rule = TokenStateCondition(tok_attribute='k1',
                              operator=Operators.EQUALS,
                              tok_value=None)
        token = Token(attributes={'k1': None})
        assert rule.check_condition(token=token)

    def test_rule_with_none_value_2(self):
        # rule checks for none-value but is wrong with that
        rule = TokenStateCondition(tok_attribute='k1',
                              operator=Operators.EQUALS,
                              tok_value=None)
        token = Token(attributes={'k1': 'v1'})
        assert rule.check_condition(token=token) is False

    def test_rule_with_none_value_3(self):
        # rule checks for value but finds none
        rule = TokenStateCondition(tok_attribute='k1',
                              operator=Operators.EQUALS,
                              tok_value='v1')
        token = Token(attributes={'k1': None})
        assert rule.check_condition(token=token) is False

    def test_rule_normal(self, example_token):
        assert self.example_rule.check_condition(
            token=self.example_token)