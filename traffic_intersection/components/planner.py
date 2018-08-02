# Path Planner
# Tung M. Phan
# May 15th, 2018
# California Institute of Technology

import os
import sys
sys.path.append('..')
import time
import random
import prepare.queue as queue
import prepare.car_waypoint_graph as waypoint_graph
import primitives.tubes
import numpy as np
<< << << < HEAD
import string
== == == =
import assumes.params as params
>>>>>> > source/master
if __name__ == '__main__':
    visualize = True
else:
    visualize = False

collision_dictionary = np.load('prepare/collision_dictionary.npy').item()
edge_to_prim_id = np.load('prepare/edge_to_prim_id.npy').item()


def dijkstra(start, end, graph):
    '''
    this function takes in a weighted directed graph, a start node, an end node and outputs
    the shortest path from the start node to the end node on that graph
    input:  start - start node
            end - end node
            graph - weighted directed graph
    output: shortest path from start to end node
    '''
    if start == end:  # if start coincides with end
        return 0, [start]
    else:  # otherwise
        score = {}
        predecessor = {}
        unmarked_nodes = graph._nodes.copy()  # create a copy of set of nodes in graph
        if start not in graph._nodes or end not in graph._nodes:


<< << << < HEAD
            raise SyntaxError(
                "either the start or end node is not in the graph!")
== == == =
            print(start)
            raise SyntaxError("The start node is not in the graph!")
        elif end not in graph._nodes:
            raise SyntaxError("The end node is not in the graph!")
>>>>>>> source/master
        for node in graph._nodes:
            if node != start:
                score[node] = float('inf')  # initialize all scores to inf
            else:
                score[node] = 0  # start node is initalized to 0
        current = start  # set currently processed node to start node
        while current != end:
            if current in graph._edges:
                for neighbor in graph._edges[current]:
                    new_score = score[current] + \
                        graph._weights[(current, neighbor)]
                    if score[neighbor] > new_score:
                        score[neighbor] = new_score
                        predecessor[neighbor] = current
            unmarked_nodes.remove(current)  # mark current node
            min_node = None  # find unmarked node with lowest score
            score[min_node] = float('inf')
            for unmarked in unmarked_nodes:
                # need equal sign to account to ensure dummy "None" value is replaced
                if score[unmarked] <= score[min_node]:
                    min_node = unmarked
            current = min_node  # set current to unmarked node with min score
        shortest_path = [end]
        if score[end] != float('inf'):
            start_of_suffix = end
            while predecessor[start_of_suffix] != start:
                shortest_path.append(predecessor[start_of_suffix])
                start_of_suffix = predecessor[start_of_suffix]
            # add start node then reverse list
            shortest_path.append(start)
            shortest_path.reverse()
        else:
            shortest_path = []
    return score[end], shortest_path


def get_scheduled_times(path, current_time, primitive_graph):
    '''
    this function takes in a path and computes the scheduled times of arrival at the nodes on this path
    input: path - the path whose nodes the user would like to compute the scheduled times of arrival for
    output: a tuple of scheduled times (of arrival) at each node
    '''
    now = current_time
    scheduled_times = [now]
    for prev, curr in zip(path[0::1], path[1::1]):
        scheduled_times.append(
            scheduled_times[-1] + primitive_graph._weights[(prev, curr)])
    return scheduled_times

<<<<<<< HEAD

def time_stamp_edge(path, edge_time_stamps, current_time, primitive_graph):
=======
def time_stamp_edge(path, edge_time_stamps, current_time, primitive_graph, partial = False):
>>>>>>> source/master
    '''
    given a weighted path, this function updates the edge_time_stamps set according to the given path.
    input:   path - weighted path
    output:  modifies edge_time_stamps
    '''
    scheduled_times = get_scheduled_times(
        path=path, current_time=current_time, primitive_graph=primitive_graph)
    for k in range(0, len(path)-1):
        left = k
        right = k+1
        edge = (path[left], path[right]) # only get topographical information, ignoring velocity and orientation
        start_time = scheduled_times[left]
        end_time = scheduled_times[right]
        delta_t = end_time - start_time # TODO: make this more efficient, get t_end directly?
        for segment_id in range(params.num_subprims):
            if partial and (k == len(path)-2) and (segment_id == params.num_subprims-1):
                last_int = (start_time + params.num_subprims-1/params.num_subprims * delta_t, float('inf')) # reserved for time indefinite
                stamp = last_int
            else:
                stamp = (start_time + segment_id/params.num_subprims * delta_t, start_time + (segment_id + 1)/(params.num_subprims) * delta_t) # stamp for subedge
            try:
                edge_time_stamps[(edge_to_prim_id[edge], segment_id)].add(stamp)
            except KeyError:
                edge_time_stamps[(edge_to_prim_id[edge], segment_id)] = {stamp}
    if partial:
        return edge_time_stamps, last_int
    else:
        return edge_time_stamps


def is_overlapping(interval_A, interval_B):
    '''
    this subroutine checks if two intervals intersect with each other; it returns True if
    they do and False otherwise
    input : interval_A - first interval
            interval_B - second interval
    output: is_intersecting - True if interval_A intersects interval_B, False otherwise
    '''
    is_disjoint = (interval_A[0] > interval_B[1]) or (
        interval_B[0] > interval_A[1])
    return not is_disjoint


def is_safe(path, current_time, primitive_graph, edge_time_stamps):
    now = current_time
    scheduled_times = [now]
    for left_node, right_node in zip(path[0::1], path[1::1]):
        curr_edge = (left_node, right_node)
        curr_prim_id = edge_to_prim_id[curr_edge]
        scheduled_times.append(
            scheduled_times[-1] + primitive_graph._weights[curr_edge])
        left_time = scheduled_times[-2]
        right_time = scheduled_times[-1]
        delta_t = right_time - left_time
        for ii in range(params.num_subprims):
            for colliding_id, jj in collision_dictionary[(curr_prim_id, ii)]:
                if (colliding_id, jj) in edge_time_stamps: # if current loc is already stamped
                    for interval in edge_time_stamps[(colliding_id, jj)]:
                        if is_overlapping( (left_time + (ii)/params.num_subprims * delta_t, left_time + (ii+1)/params.num_subprims * delta_t ), interval): # if the two intervals overlap
                            for last_index in range(len(scheduled_times)-2, 0, -1): # dial back and find a node where one can stay there forever and still be safe
                                last_prim_id = edge_to_prim_id[(path[last_index-1], path[last_index])]
                                last_interval = (scheduled_times[last_index], float('inf'))
                                overlapping = False
                                for col_id, jjj in collision_dictionary[(last_prim_id, params.num_subprims-1)]:
                                    if (col_id, jjj) in edge_time_stamps: # if current loc is already stamped
                                        for inner_interval in edge_time_stamps[(col_id, jjj)]:
                                            overlapping = overlapping or is_overlapping(last_interval, inner_interval) # if the two intervals overlap
                                if not overlapping:
                                    return False, last_index
                            overlapping = False
                            first_prim_id = edge_to_prim_id[(path[0], path[1])]
                            last_interval = (scheduled_times[0], float('inf'))
                            for col_id, jjj in collision_dictionary[(first_prim_id, 0)]:
                                if (col_id, jjj) in edge_time_stamps: # if current loc is already stamped
                                    for curr_interval in edge_time_stamps[(col_id, jjj)]:
                                        overlapping = overlapping or is_overlapping(last_interval, curr_interval) # if the two intervals overlap
                            if not overlapping:
                                return False, 0
                            return False, None
    return True, None


def print_state():
    print('The current request queue state is')
    request_queue.print_queue()


def generate_license_plate():
    choices = string.digits + string.ascii_uppercase
    plate_number = ''
    for i in range(0, 7):
        plate_number = plate_number + random.choice(choices)
    return plate_number
