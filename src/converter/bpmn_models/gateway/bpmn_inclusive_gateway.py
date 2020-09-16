from typing import List, Optional

from pedantic import pedantic_class

from src.converter.bpmn_models.gateway.bpmn_gateway import BPMNGateway
from src.converter.bpmn_models.bpmn_sequenceflow import BPMNSequenceFlow


@pedantic_class
class BPMNInclusiveGateway(BPMNGateway):
    def __init__(self, id: str,
                 sequence_flows_in: Optional[List[BPMNSequenceFlow]],
                 sequence_flows_out: Optional[List[BPMNSequenceFlow]]) -> None:
        super().__init__(id=id, sequence_flows_in=sequence_flows_in,
                         sequence_flows_out=sequence_flows_out)