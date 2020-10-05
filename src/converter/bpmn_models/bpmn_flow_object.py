"""
Metaclass for BPMNEvents, BPMNActivities and BPMNGateways.
BPMN2.0 specified a weird name for those elements. Dont get confused with
BPMNSequenceFlows or BPMNMessageFlows!!
All three (BPMNEvents, BPMNActivities and BPMNGateways) have the name attribute
in common.
Advantages of introducing a class for those three sub-classes is:
text analysis is always performed on them - so you have one access method for
all three.
A lot of methods expect an argument with one of those three types. Instead of
introducing a TypeVar every time, we let them expect a BPMNFlowObject.
"""
from pedantic import pedantic_class

from src.converter.bpmn_models.bpmn_element import BPMNFlowObject


@pedantic_class
class BPMNFlowObject(BPMNFlowObject):
    def __init__(self, id_: str, name: str) -> None:
        super().__init__(id_=id_)
        self.name = name