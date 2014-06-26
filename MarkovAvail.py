#!/usr/bin/python
#

"""
    This class accepts Markov Availability models (in the dot
    input language for describing directed graphs), and solves
    them:
"""

# TODO
#   add support for sorting output by occupancy
#   add support for performance as well as availability
#

import pydot                # pydot file parser
import operator             # list sorting
from numpy import matrix    # matrix inversion


def unquote(string):
    """
        utility function to remove the quotes around a quoted string

        Necessary because the dot input language allows identifiers
        to be qoted, and the pydot parser does not remove them.
    """
    if string.startswith('"') and string.endswith('"'):
        return string[1:-1]
    else:
        return string


def timeconvert(string, unit=60 * 60):
    """
        utility function to take a time expression (with a unit suffix)
        and convert it to the specified unit (specified in seconds)
    """
    if string.isdigit():        # default units
        v = int(string) * unit
    elif string.endswith('s'):  # seconds
        v = int(string[0:-1])
    elif string.endswith('m'):  # minutes
        v = int(string[0:-1]) * 60
    elif string.endswith('h'):  # hours
        v = int(string[0:-1]) * 60 * 60
    elif string.endswith('d'):  # days
        v = int(string[0:-1]) * 24 * 60 * 60
    elif string.endswith('w'):  # weeks
        v = int(string[0:-1]) * 7 * 24 * 60 * 60
    elif string.endswith('y'):  # years
        v = int(string[0:-1]) * 365.25 * 24 * 60 * 60
    else:
        print("ERROR ... unknown time unit (%s)" % (string))
        v = unit

    return float(v) / unit


class MarkovAvail:
    """
        Markov Availability model based on dot directed graph

            .numstates ...      number of states in the model
            .stateNums[] ...    state name to number map
            .stateNames[#] ...  state number to name map
            .stateType[#] ...   bucket names for each state
            .rates[i][j] ...    transitions i->j (in FITs)
            .occupancy[#] ...   fractional occupancy of states

    """

    def addState(self, name, stateClass):
        """ add a state to our table if it is not already there """

        # if it is already in the table, we are done
        if not name in self.stateNums:
            if self.debug > 0:
                print("    state[%d] = %s(%s)" %
                      (self.numstates, name, stateClass))
            self.stateNums[name] = self.numstates
            self.stateNames[self.numstates] = name
            self.stateType[self.numstates] = stateClass
            self.numstates += 1

    def addTransition(self, source, dest, label, value):
        """ add a transition to our table """
        if self.debug > 0:
            print("    %s -> %s [%s=%d]" % (source, dest, label, value))
        self.rates[self.stateNums[source]][self.stateNums[dest]] = value

    def __init__(self, graph, values=None, debug=0):
        """ process graph to extract states and transition rates """

        # initialize all the class attributes
        self.numstates = 0
        self.stateNames = {}
        self.stateType = {}
        self.stateNums = {}
        self.debug = debug

        # get the node and edge sets
        nodes = graph.get_node_list()
        edges = graph.get_edge_list()

        # enumerate the nodes
        if self.debug > 0:
            print("\nStates:")
        for n in nodes:
            name = n.get_name()
            if name is not 'node':
                c = n.get('state')
                t = None if c is None else unquote(c)
                self.addState(unquote(name), t)

        # look for states we didn't find in the nodes
        for e in edges:
            # make sure we know about the states
            s = unquote(e.get_source())
            self.addState(s, None)
            d = unquote(e.get_destination())
            self.addState(d, None)

        # create the transition rate matrix
        self.rates = [[0 for x in range(self.numstates)]
                      for x in range(self.numstates)]

        # fill in the transition rates
        if self.debug > 0:
            print("\nTransitions:")
        for e in edges:
            s = unquote(e.get_source())
            d = unquote(e.get_destination())
            l = unquote(e.get('label'))

            # get the time/rate and turn it into a FIT
            v = 0
            r = e.get('rate')
            f = e.get('fits')
            t = e.get('time')
            if f is not None:           # already FITs
                x = unquote(f)
                if not x.isdigit():
                    print("ERROR - FIT rate (%s) must be an integer" % (x))
                else:
                    v = int(x)
                    self.addTransition(s, d, l, v)
            elif r is not None:         # rate is same as FITs
                x = unquote(r)
                if not x.isdigit():
                    print("ERROR - rate (%s) must be an integer" % (x))
                else:
                    v = int(x)
                    self.addTransition(s, d, l, v)
            elif t is not None:         # convert time to rate
                x = unquote(t)
                if not x.isdigit() and not x[0:-1].isdigit():
                    print("ERROR - FIT rate (%s) must be <integer><unit>" %
                          (x))
                else:
                    v = 1E9 / timeconvert(x, 60 * 60)
                    self.addTransition(s, d, l, v)
            elif values is not None and l in values:   # value in dictionary
                x = values[l]
                if x.isdigit():             # a straight number (rate)
                    v = int(x)
                    self.addTransition(s, d, l, v)
                elif x[0:-1].isdigit():     # a time with a unit suffix
                    v = 1E9 / timeconvert(x, 60 * 60)
                    self.addTransition(s, d, l, v)
                else:
                    print("ERROR - bad value in dictionary: %s->%s (%s=%s)" %
                          (s, d, l, x))
            else:
                print("ERROR - no transition rate for %s: %s->%s" %
                      (l, s, d))

    def solve(self):
        """
            convert transition rates into simultaneous linear equations
                1: sum of all occupancies = 1
                2-n: sum of inputs - sum of outputs = 0

            note: we can't just use the original N equations because
                  they are not truly independent (the graph being
                  closed)
        """
        eqns = [[0 for x in range(self.numstates)]
                for x in range(self.numstates)]

        # first equation: all terms sum to one
        eqns[0] = [1 for x in range(self.numstates)]

        # sum of inputs - outputs = 0
        for s in range(1, self.numstates):
            outputs = self.rates[s]
            for d in range(0, self.numstates):
                if s == d:
                    eqns[s][d] = -sum(outputs)
                else:
                    eqns[s][d] = self.rates[d][s]

        if self.debug > 1:
            print("\nEquations:")
            print eqns

        # now solve the system of equations
        m = matrix(eqns)
        i = m.I
        if self.debug > 1:
            print("\nInverse:")
            print i

        # copy out the solutions
        self.occupancy = [0 for x in range(self.numstates)]
        l = i.tolist()
        for s in range(self.numstates):
            self.occupancy[s] = l[s][0]


def processFile(filename, dictionary=None, debug=0, deminimus=0.0000001):
    """
        parse a file, solve the model, print out the results
            name of the "dot" graph file to process
            name of the associated rate dictionary file
            level of desired debugging
            deminimums occupancy (below which we don't report)
    """
    g = pydot.graph_from_dot_file(filename)
    # FIX ... can I get pydot to parse stdin?

    if debug > 1:
        n = g.get_name()
        print("Markov Model: %s" % (n))

    # assemble an external dictionary for unspecified values
    valueDict = {}
    if dictionary is not None:
        if debug > 1:
            print("Using value dictionary: %s" % (dictionary))
        with open(dictionary) as f:
            for line in f:
                # skip comment lines
                if line.startswith('#') or line.startswith('/'):
                    continue
                # a value line needs at least two fields
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0]
                    value = parts[1]
                    valueDict[key] = value
                    if debug > 1:
                        print("    dictionary[%s]:\t%s" % (key, value))

    # process the model
    m = MarkovAvail(g, valueDict, debug)
    if debug > 1:
        print("\nFIT Rates:")
        for i in range(m.numstates):
            print m.rates[i]

    # solve the model and print the results
    m.solve()
    print("\nState Occupancy:")

    # extract the state and class occupancies
    weighted = m.rates
    stateOccupancies = {}
    classOccupancies = {}
    totalOccupancy = 0
    for i in range(m.numstates):
        o = m.occupancy[i]
        # create an occupancy weighted transition table
        for j in range(m.numstates):
            weighted[i][j] *= o
        # record all non-trivial occupancies (by both state and class)
        if o > deminimus:
            stateOccupancies[i] = o
            totalOccupancy += o
            t = m.stateType[i]
            if t in classOccupancies:
                classOccupancies[t] += o
            else:
                classOccupancies[t] = o

    # sort the states and classes by descending occupancy
    sortedStates = sorted(stateOccupancies.iteritems(),
                           key=operator.itemgetter(1),
                           reverse=True)
    sortedClasses = sorted(classOccupancies.iteritems(),
                           key=operator.itemgetter(1),
                           reverse=True)

    # print out the individual state occupancies
    for (k, o) in sortedStates:
        n = m.stateNames[k]
        t = m.stateType[k]
        print("    %08.5f%%\t%s(%s)" % (o * 100, n, t))

        # print out the tributary transition rates
        total = 0
        for (j, x) in sortedStates:
            total += weighted[j][k]
        if total > 0:
            for (j, x) in sortedStates:
                w = weighted[j][k]
                p = 100 * w / total
                if w >= 1:
                    print("           \t%05.2f%%  (%d)  from %s" %
                          (p, w, m.stateNames[j]))
    print("    --------\t------")
    print("    %8.5f%%\t%s" % (100 * totalOccupancy, "Total"))

    # print out the overall state class occupancy
    print("\nAvailability class occupancy:")
    for (k, o) in sortedClasses:
        print("    %08.5f%%\t%s" % (100 * o, k))

    print("    --------\t------")
    print("    %8.5f%%\t%s" % (100 * totalOccupancy, "Total"))


#
# this main routine serves three purposes:
#   a unit test case
#   sample code using the MarkovAvail class
#   a useful program to produce the most likely desired output
#
if __name__ == '__main__':
    """ CLI entry point:
        process command line arguments, and process the selected files
    """

    # process the command line arguments
    from optparse import OptionParser

    umsg = "usage: %prog [options] input_file [dictionary]"
    parser = OptionParser(usage=umsg)
    parser.add_option("-d", "--debug", type="int", dest="debug",
                      default="0")
    parser.add_option("-D", "--dictionary", type="string",
                      dest="dictionary")
    (opts, files) = parser.parse_args()

    if len(files) < 1:
        print("ERROR: no input file specified")
    elif opts.dictionary is not None:
        processFile(files[0], opts.dictionary, opts.debug)
    elif len(files) > 1:
        processFile(files[0], files[1], opts.debug)
    else:
        processFile(files[0], None, opts.debug)
