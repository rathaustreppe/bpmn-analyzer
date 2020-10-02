from src.models.token import Token
from src.nlp.rule_finder import RuleFinder


class TestRuleFinder:
    def test_increment(self, nn_chunker):
        # if increment (usually '++') is in the text, make no
        # chunking, instead just return th TokenStateRule which can
        # be used to increment the token attribute
        tok_attribute = 'k1'
        value = '0'

        rule_finder = RuleFinder(chunker=nn_chunker, ruleset=[])
        tsr_list = rule_finder.find_rules(text=f'{tok_attribute} ++')

        assert len(tsr_list) == 1
        tsr = tsr_list[0]

        token = Token(attributes={tok_attribute: value})
        return_token = tsr.check_and_modify(token=token)

        assert return_token.attributes[tok_attribute] == str((int(value)+1))