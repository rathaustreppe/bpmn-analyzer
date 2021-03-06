import logging
from typing import List, Union, Optional, Set, Tuple

from pedantic import pedantic_class

from src.converter.bpmn_models.bpmn_activity import BPMNActivity
from src.converter.bpmn_models.bpmn_flow_object import BPMNElement
from src.converter.bpmn_models.bpmn_model import BPMNModel
from src.converter.bpmn_models.flows.bpmn_sequenceflow import BPMNSequenceFlow
from src.converter.bpmn_models.event.bpmn_endevent import BPMNEndEvent
from src.converter.bpmn_models.event.bpmn_startevent import BPMNStartEvent
from src.converter.bpmn_models.gateway.bpmn_exclusive_gateway import \
    BPMNExclusiveGateway
from src.converter.bpmn_models.gateway.bpmn_gateway import BPMNGateway
from src.converter.bpmn_models.gateway.bpmn_inclusive_gateway import \
    BPMNInclusiveGateway
from src.converter.bpmn_models.gateway.bpmn_parallel_gateway import \
    BPMNParallelGateway
from src.exception.gateway_errors import ExclusiveGatewayBranchError, \
    JoiningGatewayError, NoBranchingGatewayError, BranchingGatewayError
from src.exception.model_errors import MultipleStartEventsError, \
    NoStartEventError
from src.exception.wrong_type_errors import NotImplementedTypeError
from src.models.running_token import RunningToken
from src.models.stack import Stack
from src.models.token_state_rule import TokenStateRule
from src.nlp.rule_finder import RuleFinder


@pedantic_class
class GraphPointer:
    """
    GraphPointer is the object that points to a
    single vertex in the BPMN-graph and reads its values
    to change the RunningToken attributes --> the tokens current
    state. It knows how to deal with gateways.
    """

    def __init__(self,
                 token: RunningToken,
                 ruleset: List[TokenStateRule],
                 model: BPMNModel) -> None:
        self.model = model
        self.token = token
        self.rule_finder = RuleFinder(ruleset=ruleset)
        self.stack = Stack[Union[BPMNElement]]()
        self._model_start = None
        self.processed_flows: Set[BPMNSequenceFlow] = set()

        if self.stack is None:
            self.stack = Stack()

    def iterate_model(self, number_of_steps: Optional[int] = 0) -> Tuple[int, RunningToken]:
        """
        Iterates through the BPMNModel, analyses the texts
        and performs state transitions on RunningToken.
        Returns a tuple containing the information:
        int: 0 if processing was ok, 1 if processing took to many steps. This
        is an indicator of an infinite loop.
        Token: the modified RunningToken
        """

        # specify how many steps are done before
        # quitting. This prevents infinite loops and is easier to implement
        # then an infinite-loop-detector.
        if number_of_steps == 0:
            number_of_steps = len(self.model.bpmn_elements) * 5

        for _ in range(number_of_steps):

            if self._model_start is None:
                # init
                self._model_start = self.find_start_event()
                self.next_step_no_gateway(element=self._model_start)

            if not self.reached_end_event():
                # continue processing of diagram
                self.next_step_switch_by_type()
            else:
                # reached end event. Analyse end event and then quit.
                # Return ok.
                self.next_step_switch_by_type()
                self.stack.empty()
                return (0, self.token)

        # loop end reached but not the diagram end: something went wrong
        return (-1, self.token)


    def reached_end_event(self) -> bool:
        return isinstance(self.stack.top(), BPMNEndEvent)

    def find_start_event(self) -> BPMNStartEvent:
        """
        Find the entry point of the BPMNModel from where
        the BPMNModel is read. This is usually the BPMNStartEvent.
        """
        start = self.model.find_elements_by_type(type_to_find=BPMNStartEvent)
        if len(start) == 1:
            return start[0]
        elif len(start) == 0:
            raise NoStartEventError(model=self.model)
        else:
            raise MultipleStartEventsError(model=self.model)

    def _modify_token_with_rules(self,
                                 matching_rules: List[TokenStateRule]) -> RunningToken:
        """
        We apply rules (==change token state), when their SynonymClouds are
        matching and their conditions are true.
        """
        for rule in matching_rules:
            self.token = rule.check_and_modify(token=self.token)
        return self.token

    @staticmethod
    def first_element_of_all_branches(branches: List[BPMNSequenceFlow]) -> \
            List[Optional[BPMNElement]]:
        return [flow.target for flow in branches]

    def condition_fulfilling_sequence_flows(self,
                                            flows_to_check: List[
                                                BPMNSequenceFlow]) \
            -> List[BPMNSequenceFlow]:
        """
        Checks flow-conditions of all given sequenceFlows. This is needed
        for gateways to check which flows meet their branching conditions.
        Every flow without a condition (==None) is treated as if it would have
        a fulfilled condition. This behaviour is aligned to normal BPMN-Diagrams
        where not all sequenceFlows have conditions (e.g. activity-flow-activity)
        """
        flows = []
        for flow in flows_to_check:
            if flow.condition is None or flow.condition.check_condition(
                    token=self.token) is True:
                # we treat flows without conditions as fulfilled flows
                flows.append(flow)
        return flows

    def collect_conditional_sequence_flows_of_gateway(self,
                                                      gateway: BPMNGateway) -> \
            List[BPMNSequenceFlow]:
        """
        Method that makes a distinction of different gateway types and returns
        the corresponding sequence_flows that fulfill the conditions.
        Parallel-Gateway: returns all sequence_flows
        Inclusive-Gateway: returns all sequence_flows that meet the condition
        Exclusive-Gateway: checks that only one sequence_flow
        fulfills the condition
        """
        flows = gateway.sequence_flows_out

        if isinstance(gateway, BPMNParallelGateway):
            return flows

        elif isinstance(gateway, BPMNInclusiveGateway):
            return self.condition_fulfilling_sequence_flows(
                flows_to_check=flows)

        elif isinstance(gateway, BPMNExclusiveGateway):
            cond_flows = self.condition_fulfilling_sequence_flows(
                flows_to_check=flows)
            if len(cond_flows) == 1:
                return cond_flows
            elif len(cond_flows) >1:
                raise ExclusiveGatewayBranchError(gateway=gateway,flows=flows)
            else:
                raise BranchingGatewayError(gateway=gateway)

    def text_analysis(self, current: BPMNElement) -> None:
        matching_rules = self.rule_finder.find_rules(text=current.name)
        self._modify_token_with_rules(matching_rules=matching_rules)

    def all_incoming_flows_processed(self,
                                     gateway: BPMNParallelGateway) -> bool:
        for flow in gateway.sequence_flows_in:
            if flow not in self.processed_flows:
                return False
        return True

    def get_inflows(self, element: BPMNElement) -> List[BPMNSequenceFlow]:
        if isinstance(element, BPMNGateway):
            return element.sequence_flows_in
        elif isinstance(element, BPMNActivity):
            return [element.sequence_flow_in]
        elif isinstance(element, BPMNEndEvent):
            return [element.sequence_flow]
        else:
            raise NotImplementedTypeError(object_=element)

    def next_step_exclusive_gateway(self,
                                    gateway: BPMNExclusiveGateway) -> None:
        """
        Exclusive gateways have no need to check incoming flows, they
        directly go into 'output mode'.
        """
        if gateway.is_branching_gateway():
            self.branching_gateway(gateway=gateway)
        else:
            # joining exclusive gateway need no condition check
            self.stack.push(item=gateway.sequence_flows_out[0].target)
            self.processed_flows.add(gateway.sequence_flows_out[0])

    def next_step_parallel_gateway(self, gateway: BPMNParallelGateway) -> None:
        """
        Method to deal with branching and joining parallel gateways.
        Branching parallel gateways have only one incoming flow.
        Joining parallel gateways need check if all their incoming gateways
        have been processed.
        """
        if gateway.is_branching_gateway():
            self.branching_gateway(gateway=gateway)
        else:
            # joining gateway
            if self.all_incoming_flows_processed(gateway=gateway):
                # push the single outgoing flow
                if len(gateway.sequence_flows_out) == 1:
                    self.stack.push(item=gateway.sequence_flows_out[0].target)
                else:
                    raise JoiningGatewayError(gateway=gateway)
            else:
                # not all incomming flows processed = continue with other flows
                # therefore nothing to do now
                pass

    def next_step_inclusive_gateway(self,
                                    gateway: BPMNInclusiveGateway) -> None:
        """
        Method to deal with BPMNInclusiveGateways. Branching gateways have
        their standard treatment but joining gateways are interesting:
        They have multiple incoming flows. Some of them were true and some of
        them were not. We have no tools to check that (e.g. Strongly connected
        components to detect looping incoming flows). We can only assert that
        if the stack is empty, there are no other things to process. This means
        all incoming flows were already processed. So we can switch trough to
        output. If the stack is not empty other things need to be processed first.
        """
        if gateway.is_branching_gateway():
            self.branching_gateway(gateway=gateway)
        else:
            if self.stack.empty():
                self.stack.push(item=gateway.sequence_flows_out[0].target)
            else:
                # stack not empty: other things to process first
                # when bugs occur with this behaviour, then a look-back-mechanism
                # is neccessary and has to replace the self.stack.empty()
                # mechanism.
                pass

    def branching_gateway(self, gateway: BPMNGateway) -> None:
        """
        Checks conditions of outgoing flow and puts all those adjacent
        elements on stack where the conditions are meet.
        """
        if gateway.is_branching_gateway():
            conditions_meet_flows = \
                self.collect_conditional_sequence_flows_of_gateway(
                    gateway=gateway)
            branch_elements = self.first_element_of_all_branches(
                branches=conditions_meet_flows)

            # reverse list order to put it 1:1 on stack (because stack is LIFO,
            # but first list element should be on top of stack, because easier
            # to debug)
            branch_elements.reverse()
            for element in branch_elements:
                self.stack.push(item=element)

            # processed flows
            for flow in conditions_meet_flows:
                self.processed_flows.add(flow)
        else:
            raise NoBranchingGatewayError(gateway=gateway)


    def next_step_no_gateway(self, element: BPMNElement) -> None:
        """
        Method that knows how to deal with every other BPMN-Element except
        gateways and flows. Those BPMNElements (BPMNActivity, BPMNStartEvent,
        BPMNEndEvent) have only one adjacent element and need text processing
        (NLP). There is no enhanced stack logic in this function: after NLP
        only put the adjacent element on top of the stack.
        """

        # just a little helper function to make the code lines more readable
        def push(to_push: BPMNElement):
            self.stack.push(item=to_push)

        # perform text analysis and change the token state if the text is not
        # empty. If the text is empty, leave it.
        if element.name is not None and not element.name == '':
            self.text_analysis(current=element)

        # Push the next element on stack. We make a distinction of different
        # types here, because accessing the outgoing flow depends on the type.
        # Unifying the access of the flow is not possible: BPMNStartEvents have
        # only one flow, BPMNActivities incomming and outgoing flows.
        if isinstance(element, BPMNActivity):
            push(to_push=element.sequence_flow_out.target)
            self.processed_flows.add(element.sequence_flow_out)

        elif isinstance(element, BPMNStartEvent):
            push(to_push=element.sequence_flow.target)
            self.processed_flows.add(element.sequence_flow)

        elif isinstance(element, BPMNEndEvent):
            # BPMNEndEvent on top of stack is treated as ending in next
            # iteration.
            push(to_push=element)

    def next_step_switch_by_type(self) -> None:
        """
        >>Main entry point of algorithm<<
        Checks the type of the current element to be processed and calls the
        proper methods.

        >>When calling first<<
        make sure self.stack has an element on top - which
        is usually the BPMNStartEvent.

        >>General design pattern<<
        Each element knows best how to be processed. So every element is
        processed by a different method. Element types that logically belong
        together are processed together (e.g. Activities and StartEvents).

        GraphPointer works sequentially: with every call it goes one step
        further (= processes one BPMNFlowObject). There are no threads involved e.g.
        when BPMNGateways split into multiple branches.

        As the BPMN-Specification we make a distinction between branching and
        joining gateways. Branching gateways have one input and split it up
        depending on the flow-conditions and the gateway type. The joining
        gateways collect multiple inputs and have one outgoing flow. A mix
        of both is not allowed.

        To know which element is next GraphPointer involves the stack. Every
        element-processing method needs to put the next element on the stack.
        This is easy for a chain of BPMNActivities (because they have only one
        outgoing sequence flow). But this is a little more complicated with
        BPMNGateways. There it is necessary to have different logic depending
        on the type of the gateway. Take a look at the gateway methods to
        find out more.

        We keep track of a set of 'processed sequence flows'. Those are flows
        that were processed. This is mainly needed for the joining
        BPMNInclusiveGateway.
        """
        current = self.stack.pop()
        logging.debug(f'Processing BPMNElement: {current}')

        inflows_of_current = self.get_inflows(element=current)

        # If we reached the current element we can mark the incoming sequence
        # flow as processed. This is easy if there is only one incoming flow.
        # We do this in case the element-processing method forgot to mark the
        # outgoing flow as processed OR the previous element was a gateway
        # with several outgoing flows and we want to mark each of the flows
        # one by one only at the time when they are processed - which is
        # right now.
        if len(inflows_of_current) == 1:
            self.processed_flows.add(inflows_of_current[0])

        # If current is a BPMNGateway and has only one outgoing flow we can
        # mark the flow as processed as well. We do this here in case the
        # BPMNGateway-processing methods forget about this. (The data structure
        # is a set which has no costs of adding the same element multiple times)
        if isinstance(current, BPMNGateway) and len(
                current.sequence_flows_out) == 1:
            self.processed_flows.add(current.sequence_flows_out[0])

        # Call the element-processing methods.
        if isinstance(current, BPMNExclusiveGateway):
            self.next_step_exclusive_gateway(gateway=current)
        elif isinstance(current, BPMNParallelGateway):
            self.next_step_parallel_gateway(gateway=current)
        elif isinstance(current, BPMNInclusiveGateway):
            self.next_step_inclusive_gateway(gateway=current)
        else:
            self.next_step_no_gateway(element=current)
