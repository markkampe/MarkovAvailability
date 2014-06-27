"""
    This class accepts Markov Availability models (in the dot
    input language for describing directed graphs), and solves
    them:
"""


import pydot                # pydot file parser
import operator             # list sorting
from numpy import matrix    # matrix inversion


def unquote(string):
    """
        utility function to remove the quotes around a quoted string

        Necessary because the dot input language allows identifiers
        to be qoted, and the pydot parser does not remove the quotes.

        Args:
            string (string): the string to be unquoted

        Returns:
            string: the string w/o surrounding quotes (if any)
    """
    if string is None:
        return None
    if string.startswith('"') and string.endswith('"'):
        return string[1:-1]
    else:
        return string


def timeconvert(string, unit=60 * 60):
    """
        utility function convert a time expression to a specified unit

        Args:
            string (string): the expression to be converted
            unit (int): unit (in seconds) of desired result

        Returns:
            int: number of time units specified by input string
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

        Attributes (basic information about the states):
            .numstates ...      number of states in the model
            .stateNums[name] .. state name to number map
            .stateNames[#] ...  state number to name map

       Attributes (information parsed from the input file):
            .stateType[#] ...   bucket names for each state
            .statePerf[#] ...   the stated performance level for this state
            .stateCap[#] ...    the stated capacity level for this state
            .rates[i][j] ...    transitions i->j (in FITs)

       Attributes (rates and solutions):
            .occupancy[#] ...   fractional occupancy of each state
            .weighted[i][j] ..  occupancy weighted transition rates
                                (rate times source state occupancy)

        Note that the order of the entries in these arrays is arbitrary
        (assigned by the pydot parser).  If you want the results sorted
        by class, by name, or by occupancy, you must do that yourself.

    """

    def addState(self, name, stateClass=None, statePerf=None, stateCap=None):
        """ add a state to our table (if it is not already there)

            Args:
                name (string): name of this state
                stateClass (string):    availability class
                statePerf(string):      performance of this state
                stateCap(string):       capacity of this state

                All arguments other than the name are optional, and are
                not used in this class.  We merely parse them and make
                them available to the client (for reporting purposes).
        """

        # if it is already in the table, we are done
        if not name in self.stateNums:
            i = self.numstates
            self.stateNums[name] = i
            self.stateNames[i] = name
            self.numstates += 1

            if self.debug > 0:
                print("    state[%d] = %s(%s,%s,%s)" %
                      (i, name, stateClass, statePerf, stateCap))

            # update the state annotations we collect for the client
            if stateClass is not None:
                self.stateType[i] = stateClass
            if statePerf is not None:
                self.statePerf[i] = statePerf
            if stateCap is not None:
                self.stateCap[i] = statPerf

    def addTransition(self, source, dest, label, value):
        """ add a transition to our table

            Args:
                source (int): initial state for this transition
                dest (int): target state for this transition
                label (string): name associated with this transition
                value (int): rate (in FITs) asssociated with this transition
        """
        if self.debug > 0:
            print("    %s -> %s [%s=%d]" % (source, dest, label, value))
        self.rates[self.stateNums[source]][self.stateNums[dest]] = value

    def __init__(self, graph, values=None, debug=0):
        """ process graph to extract states and transition rates

            Args:
                graph (pydot graph): the Markov graph to be solved
                values (dictionary): transition rate value lookup
                debug (int): desired level of debug output
                    0:  none
                    1:  basic parameters
                    2:  painful details
        """

        if debug > 0:
            n = graph.get_name()
            print("\nMarkov Model: %s" % (n))

        # initialize all the class attributes
        self.numstates = 0
        self.stateNames = {}        # number to name map
        self.stateNums = {}         # name to number map
        self.stateType = {}         # parsed for use by client
        self.statePerf = {}         # parsed for use by client
        self.stateCap = {}          # parsed for use by client
        self.debug = debug

        # get the node and edge sets
        nodes = graph.get_node_list()
        edges = graph.get_edge_list()

        # enumerate the nodes
        if self.debug > 0:
            print("\nStates:")
        for n in nodes:
            name = unquote(n.get_name())
            if name is not 'node':
                # capture per-state attributes the client might want
                t = unquote(n.get('state'))
                p = unquote(n.get('performance'))
                c = unquote(n.get('capacity'))
                self.addState(name, t, p, c)

        # look for undeclared states implied by the transitions
        for e in edges:
            self.addState(unquote(e.get_source()))
            self.addState(unquote(e.get_destination()))

        # now that we know how many states, create transition rate matrix
        self.rates = [[0 for x in range(self.numstates)]
                      for x in range(self.numstates)]

        # fill in the transition rates
        if self.debug > 0:
            print("\nTransitions:")
        for e in edges:
            s = unquote(e.get_source())
            d = unquote(e.get_destination())
            l = unquote(e.get('label'))

            # see if a rate has been specified
            f = unquote(e.get('fits')) or unquote(e.get('rate'))
            t = unquote(e.get('time'))
            if f is not None:           # a numeric rate
                if not f.isdigit():
                    print("ERROR - rate (%s) must be an integer" % (f))
                else:
                    self.addTransition(s, d, l, int(f))
            elif t is not None:         # a numeric time
                if not t.isdigit() and not t[0:-1].isdigit():
                    print("ERROR - time (%s) must be <#><unit>" % (t))
                else:
                    v = 1E9 / timeconvert(t, 60 * 60)
                    self.addTransition(s, d, l, v)
            elif values is not None and l in values:   # value in dictionary
                x = values[l]
                if x.isdigit():             # a straight number (rate)
                    self.addTransition(s, d, l, int(x))
                elif x[0:-1].isdigit():     # a time with a unit suffix
                    v = 1E9 / timeconvert(x, 60 * 60)
                    self.addTransition(s, d, l, v)
                else:
                    print("ERROR - bad value in dictionary: %s->%s (%s=%s)" %
                          (s, d, l, x))
            else:
                print("ERROR - no transition rate for %s: %s->%s" % (l, s, d))

        if self.debug > 1:
            print("\nDEBUG: Raw Transition Rates:")
            for i in range(self.numstates):
                print self.rates[i]

    def solve(self):
        """
            convert transition rates into simultaneous linear equations
                1: sum of all occupancies = 1
                2-n: sum of inputs - sum of outputs = 0

            note: we can't just use the original N equations because
                  they are not truly independent (the graph being
                  closed)
        """
        # start out with all zeroes
        eqns = [[0 for x in range(self.numstates)]
                for x in range(self.numstates)]

        # first equation: all terms sum to one
        eqns[0] = [1 for x in range(self.numstates)]

        # remaining equations: sum of inputs - outputs = 0
        for s in range(1, self.numstates):
            outputs = self.rates[s]
            for d in range(0, self.numstates):
                if s == d:
                    eqns[s][d] = -sum(outputs)
                else:
                    eqns[s][d] = self.rates[d][s]

        # now solve the system of equations
        m = matrix(eqns)
        inv = m.I
        if self.debug > 1:
            print("\nDEBUG: Equations:")
            for i in range(self.numstates):
                print eqns[i]
            print("\nDEBUG: Inverse:")
            for i in range(self.numstates):
                print inv[i]

        # copy the Matrix solutions back into lists for the client
        self.occupancy = [0 for x in range(self.numstates)]
        l = inv.tolist()
        for s in range(self.numstates):
            self.occupancy[s] = l[s][0]

        # compute occupancy weighted transition rates
        self.weighted = self.rates
        for s in range(self.numstates):
            o = self.occupancy[s]
            for j in range(self.numstates):
                self.weighted[s][j] *= o


def processFile(filename, dictionary=None, debug=0):
    """
        parse a file, solve the model, print out the results

        This is a useful function in its own right, used to implement a
        Markov Model solving CLI.  But it is also an example of how to
        use the MarkovAvail class and make sense of the results.

        Args:
            filename (string): name of dot format input file
            dictionary (string): name of transition rates file
            debug (int): level of desired debug output
                0:  none
                1:  parsed and interpreted parameters
                2:  painful for code (not model) debugging
            name of the "dot" graph file to process
            name of the associated rate dictionary file
            level of desired debugging

        Returns:
            MarkovAvail: parameters and solutions
            list: sorted (state #, occupancy) tupples
    """
    # process the input file
    g = pydot.graph_from_dot_file(filename)

    # process the dictionary
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

    # solve the model and print the results
    m.solve()

    # create a list of states, sorted by occupancy
    stateOccupancies = {}
    for i in range(m.numstates):
        o = m.occupancy[i]
        stateOccupancies[i] = o
    sortedStates = sorted(stateOccupancies.iteritems(),
                          key=operator.itemgetter(1),
                          reverse=True)

    # return the solution and the sorted state/occupancy list
    return (m, sortedStates)
