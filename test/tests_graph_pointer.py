from copy import copy

import igraph
import pytest

from src.converter.bpmn_models.bpmn_enum import BPMNEnum
from src.graph_pointer import GraphPointer
from src.models.graph_text import GraphText
from src.models.token import Token
from src.models.token_state_modification import TokenStateModification


class TestGraphPointer:

    def run_pointer(self, graph_pointer: GraphPointer) -> Token:
        for i in range(100):
            ret = graph_pointer.runstep_graph()
            if ret == 1:
                return graph_pointer.get_token()
            i += 1
        # if graph_pointer does not hold after 100 steps
        return Token(attributes=None)

    def test_bill_process1(self, bill_process_chunker,
                          bill_process_ruleset,
                          bill_process_init_token,
                          bill_process_solution_token):
        # bill first arrives in goerlitz
        pre = TokenStateModification(key='place', value='Goerlitz')
        bill_process_init_token.change_value(modification=pre)

        graph = igraph.Graph()
        graph = graph.as_directed()

        graph.add_vertices(5)
        graph.add_edges([(0, 1), (1, 2), (2, 3), (3, 4)])

        graph.vs[0][BPMNEnum.NAME.value] = GraphText(text="ML signs bill")
        graph.vs[1][BPMNEnum.NAME.value] = GraphText(text="send bill to Zittau")
        graph.vs[2][BPMNEnum.NAME.value] = GraphText(text='Zittau checks contract')
        graph.vs[3][BPMNEnum.NAME.value] = GraphText(text='Zittau signs bill')
        graph.vs[4][BPMNEnum.NAME.value] = GraphText(text='send bill to Dresden')

        graph_pointer = GraphPointer(graph=graph, token=bill_process_init_token,
                                     ruleset=bill_process_ruleset,
                                     chunker=bill_process_chunker)
        return_token = self.run_pointer(graph_pointer=graph_pointer)
        assert return_token == bill_process_solution_token

    def test_bill_process2(self, bill_process_chunker,
                          bill_process_ruleset,
                          bill_process_init_token,
                          bill_process_solution_token):
        graph = igraph.Graph()
        graph = graph.as_directed()

        graph.add_vertices(5)
        graph.add_edges([(0, 1), (1, 2), (2, 3), (3, 4)])

        graph.vs[0][BPMNEnum.NAME.value] = GraphText(text='Zittau checks contract')
        graph.vs[1][BPMNEnum.NAME.value] = GraphText(text='Zittau signs bill')
        graph.vs[2][BPMNEnum.NAME.value] = GraphText(text="send bill to Goerlitz")
        graph.vs[3][BPMNEnum.NAME.value] = GraphText(text="ML signs bill")
        graph.vs[4][BPMNEnum.NAME.value] = GraphText(text='send bill to Dresden')

        graph_pointer = GraphPointer(graph=graph, token=bill_process_init_token,
                                     ruleset=bill_process_ruleset,
                                     chunker=bill_process_chunker)
        return_token = self.run_pointer(graph_pointer=graph_pointer)
        assert return_token == bill_process_solution_token

    def test_bill_process3(self, bill_process_chunker,
                          bill_process_ruleset,
                          bill_process_init_token,
                          bill_process_solution_token):
        # business process works

        graph = igraph.Graph()
        graph = graph.as_directed()

        graph.add_vertices(6)
        graph.add_edges(
            [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)])

        graph.vs[0][BPMNEnum.NAME.value] = GraphText(text='Zittau checks contract')
        graph.vs[1][BPMNEnum.NAME.value] = GraphText(text='Zittau signs bill')
        graph.vs[2][BPMNEnum.NAME.value] = GraphText(text="send bill to Goerlitz")
        graph.vs[3][BPMNEnum.NAME.value] = GraphText(text="ML signs bill")
        graph.vs[4][BPMNEnum.NAME.value] = GraphText(text="send bill to Zittau")
        graph.vs[5][BPMNEnum.NAME.value] = GraphText(text='send bill to Dresden')

        graph_pointer = GraphPointer(graph=graph, token=bill_process_init_token,
                                     ruleset=bill_process_ruleset,
                                     chunker=bill_process_chunker)
        return_token = self.run_pointer(graph_pointer=graph_pointer)
        assert return_token == bill_process_solution_token

    def test_bill_process4(self, bill_process_chunker,
                          bill_process_ruleset,
                          bill_process_init_token,
                          bill_process_solution_token):
        # business process doesnt work
        # ML cant sign in Zittau

        graph = igraph.Graph()
        graph = graph.as_directed()
        graph.add_vertices(4)
        graph.add_edges([(0, 1), (1, 2), (2, 3)])

        graph.vs[0][BPMNEnum.NAME.value] = GraphText(text='Zittau checks contract')
        graph.vs[1][BPMNEnum.NAME.value] = GraphText(text='Zittau signs bill')
        graph.vs[2][BPMNEnum.NAME.value] = GraphText(text='ML signs bill')
        graph.vs[3][BPMNEnum.NAME.value] = GraphText(text='send bill to Dresden')

        graph_pointer = GraphPointer(graph=graph, token=bill_process_init_token,
                                     ruleset=bill_process_ruleset,
                                     chunker=bill_process_chunker)
        return_token = self.run_pointer(graph_pointer=graph_pointer)

        assert return_token != bill_process_solution_token
        assert return_token.get_attribute(key='signature ML') == False
