from typing import List

import igraph
from igraph import Edge, Graph
from pedantic import pedantic_class

from src.converter.bpmn_models.bpmn_activity import BPMNActivity
from src.converter.bpmn_models.bpmn_enum import BPMNEnum
from src.converter.bpmn_models.gateway.bpmn_gateway import BPMNGateway
from src.models.graph_text import GraphText
from src.models.token import Token
from src.models.token_state_rule import TokenStateRule
from src.nlp.chunker import Chunker
from src.nlp.rule_finder import RuleFinder


@pedantic_class
class GraphPointer:
    """
    GraphPointer is the object that points to a
    single vertex in the BPMN-graph and reads its values
    to change the token attributes --> the tokens current
    state.
    """

    def __init__(self, graph: Graph,
                 token: Token,
                 ruleset: List[TokenStateRule],
                 chunker: Chunker) -> None:
        self.graph = graph
        self.token = token
        self.__pointer = -1
        self.rule_finder = RuleFinder(chunker=chunker, ruleset=ruleset)
        self.previous_element: igraph.Vertex = None

    def get_token(self) -> Token:
        return self.token

    def runstep_graph(self) -> int:
        """
        With each call, it iterates one step through the
        graph (= changes pointer), analyses the text (= bpmn
        activity) and performs state transitions on token.
        Returns:
            int:
            1 if the end of the graph is reached
            0 if the the step was performed successfully but
            the end of the graph is not reached yet
        """
        if self.__pointer < -1:
            raise RuntimeError(
                f'GraphPointer.__pointer {self.__pointer} '
                f'is set horribly wrong.')

        if self.__pointer == -1:
            # case: init, first call of runstep_graph
            # set pointer to first vertex of graph and
            # change the state of the token
            self.__set_start_vertex()
            self.__change_token_state()
            return 0

        # all other cases: decide what to to by outgoing edges
        edges_ids = self.graph.incident(self.__pointer, mode='OUT')

        # if there are no edges left, we are done
        if len(edges_ids) == 0:
            return 1

        # if there is one outgoing edge, set pointer to it
        # and change token state
        if len(edges_ids) == 1:
            # get the vertex the edge points to
            edge: Edge = self.graph.es[edges_ids[0]]
            vertex_id = edge.target

            self.change_pointer(vertex_id=vertex_id)
            self.__change_token_state()
            return 0

        if len(edges_ids) > 1:
            print('Token-Algo is not implemented for this case')

    def __set_start_vertex(self) -> None:
        """
        Define the entry point of the graph from where
        the graph is read. Can only process directed graphs
        and only graphs with one start vertex.
        Start vertex have no prior (incident) vertex.
        Returns: None, but changes inner pointer of GraphPointer

        """
        if not self.graph.is_directed():
            raise RuntimeError(
                'ERROR: graph is not directed')

        # get the incidence list of all verticies
        # if one and only one vertices has no incident edge,
        # it is the start vertex
        incidence_list = (self.graph.get_inclist(mode="IN"))

        # now we got something like
        # >>> [[], [0], [1], [2], [3]]
        # and want to check that there is only one empty
        # list and we want to get the position of the list
        # because this is equal to the vertex_id (see
        # documentation of igraph.graph.get_inclist)
        if (incidence_list.count([])) == 0:
            raise RuntimeError(
                'ERROR: graph has no starting point')

        if (incidence_list.count([])) > 1:
            raise RuntimeError(
                'ERROR: graph has multiple starting points')

        vertex_id = incidence_list.index([])

        # set inner pointer to starting vertex
        self.change_pointer(vertex_id=vertex_id)

    def change_pointer(self, vertex_id: int) -> None:
        """
        Changes the pointer to another vertex.
        Args:
            vertex_id (int): The ID of the vertex given by igraph-lib.
        """
        if vertex_id is None or vertex_id < 0:
            raise RuntimeError(
                'ERROR: vertex_id is invalid'
                '(None or smaller than 0')
        self.__pointer = vertex_id

    def __change_token_state(self) -> None:
        # we call this function whenever the pointer has changed
        # analyzes text and updates token
        # we apply rules (==change token state), when their synonymclouds are
        # matching and their conditions are true

        vertex = self.graph.vs[self.__pointer]
        vertex_text: GraphText = vertex[BPMNEnum.NAME.value]

        # no handling of start and end events implemented yet, skip them
        if vertex_text.get_text() == 'startendevent':
            return

        rules_with_matching_syncloud = self.rule_finder.find_rules(
            text=vertex_text)

        print(f'TEXT: {vertex_text}')
        print(f'RULES: {rules_with_matching_syncloud}')

        for rule in rules_with_matching_syncloud:
            self.token = rule.check_and_modify(token=self.token)


    
    def _next_step(self):
        # set current
        current = None
        if type(self.previous_element) == BPMNActivity:
            next_edges = self.previous_element.out_edges()
            if len(next_edges) == 1:
                current = next_edges[0].target
        elif isinstance(self.previous_element, BPMNGateway):
            current = self.stackhandler.next_element()
        else:
            raise Exception(f'Previous element {self.previous_element} is either'
                            f'activity or gateway, not {type(self.previous_element)}')

        # check current
        if type(current) == BPMNActivity:
            pass
            #text analysis & rule checking & TS Changing
        elif isinstance(current, BPMNGateway):
            pass
            # check Conditions of every branch
            # stackhandler.check_gateway(gateway, branchvertices)

        self.previous_element = current