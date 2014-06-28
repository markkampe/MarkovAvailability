#!/usr/bin/python
#
from MarkovAvail import processFile, MarkovAvail
import operator


class OutputFormat:
    """
        A dynamically created output reporting format

        Fields:
            format_s (string)   %s format for data fields
            format_n (string)   %s format for name fields
            format_h (string)   %f format for hi-res numbers
            format_l (string)   %f format for low-res numbers
            format_d (string)   %d format for integers
            format (string)     %s format for an entire line
            line (string)       separator line of data width

        Notes:
            Callers will format individual fields using the format_?,
            and then format all of the strings with the whole-line
            format.  There are a few reasons for this:
                one format works for headers, separators and data
                one format works for all data field types
                fields can easily be suppressed where inapplicable
                different formats cannot fall out of sync

    """

    def __init__(self, data=10, name=10, hires=5, lores=1, indent=4):
        """
            create an output format this report

            Args:
                num (int):          desired width of a numeric field
                name (int):         desired width of a name field
                hires (int):        decimal places for hi-res numbers
                lores (int):        decimal places for low-res numbers
                indent (int)        indent for all standad output
        """

        # individual fields will be rendered one of these formats
        self.format_h = "%" + "%d.%d" % (data - 1, hires) + "f%%"
        self.format_l = "%" + "%d.%d" % (data - 1, lores) + "f%%"
        self.format_d = "%" + "%d" % (data) + "d"
        self.format_n = "%%-%ds" % (name)
        self.format_s = "%" + "%d" % (data) + "s"

        self.line = (data - 1) * "-"                # data-width separator

        # the format for an entire output line (data, name, name, data, data)
        self.format = indent * " " + self.format_s + \
                      2 * ("\t" + self.format_n) + 2 * ("\t" + self.format_s)


def state_report(states, markov, format):
    """
        generate a basic state occupancy report

        Args:
            states (list):          an ordered list of (state, occ) tupples
            markov (MarkovAvai):    the solution to be reported
            format (OutputFormat):  the chosen output formats

        Note:
            we treat performance and capacity as per-state fractions of nominal
    """
    t_occ = 0           # total occupancy
    t_perf = 0          # total occupancy-weighted performance
    t_cap = 0           # total occupancy-weighted capacity

    # print out the individual state occupancies
    fmt = format.format
    line = format.line
    print("\nper state:")
    print(fmt % ("occupancy", "state", "class", "perf", "capacity"))
    print(fmt % (line, line, line, line, line))

    # print out the states in order
    #   and accumulate occupancy-weighted performance and capacity
    for (i, occupancy) in states:
        n = markov.stateNames[i]
        t = markov.stateType[i]
        t_occ += occupancy
        po = format.format_h % (100 * occupancy)

        # look at performance (which we treat as fractions)
        if i in markov.statePerf:
            p = float(markov.statePerf[i])
            t_perf += occupancy * p
            pp = format.format_l % (100 * p)
        else:
            pp = ""

        # look at capacity (which we treat as fractions)
        if i in markov.stateCap:
            c = float(markov.stateCap[i])
            t_cap += occupancy * c
            pc = format.format_l % (100 * c)
        else:
            pc = ""

        print(fmt % (po, n, t, pp, pc))

    # followed by a final summary
    print(fmt % (line, line, "", "", ""))
    po = f.format_h % (100 * t_occ)
    pp = "" if t_perf == 0 else format.format_l % (100 * t_perf)
    pc = "" if t_cap == 0 else format.format_l % (100 * t_cap)
    print(fmt % (po, "total", "", pp, pc))


def class_report(markov, format):
    """
        generate a class-bucket occupancy report

        Args:
            markov (MarkovAvai):    the solution to be reported
            format (OutputFormat):  the chosen output formats

        Note:
            we treat performance and capacity as per-state fractions of nominal
    """
    # run through the states, aggregating statistics by class
    #   and accumulate occupancy-weighted performance and capacity
    occ = {}            # per-class occupancies
    perf = {}           # per-class performance
    cap = {}            # per-class capacity
    for (i, occupancy) in states:
        t = markov.stateType[i]
        if t is None:
            continue

        # accumulate per-class occupancy
        if t in occ:
            occ[t] += occupancy
        else:
            occ[t] = occupancy

        # accumulate weighted per-class performance
        if i in markov.statePerf:
            if t in perf:
                perf[t] += occupancy * float(markov.statePerf[i])
            else:
                perf[t] = occupancy * float(markov.statePerf[i])

        # accumulate weighted per-class capacity
        if i in markov.stateCap:
            if t in cap:
                cap[t] += occupancy * float(markov.stateCap[i])
            else:
                cap[t] = occupancy * float(markov.stateCap[i])

    # get an occupancy sorted list of availability classes
    sortedClasses = sorted(occ.iteritems(),
                           key=operator.itemgetter(1),
                           reverse=True)

    # print out the per-class statistics
    fmt = format.format
    line = format.line
    print("\nper availability class:")
    print(fmt % ("occupancy", "", "class", "perf", "capacity"))
    print(fmt % (line, "", line, line, line))

    t_occ = 0           # total occupancy
    t_perf = 0          # total occupancy-weighted performance
    t_cap = 0           # total occupancy-weighted capacity
    for (n, occupancy) in sortedClasses:
        if occupancy == 0:
            continue
        t_occ += occupancy
        po = format.format_h % (100 * occupancy)
        if n in perf:
            p = perf[n]
            t_perf += p
            pp = format.format_l % (100 * p / occupancy)
        else:
            pp = ""
        if n in cap:
            c = cap[n]
            t_cap += c
            pc = format.format_l % (100 * c / occupancy)
        else:
            pc = ""
        print(fmt % (po, "", n, pp, pc))

    print(fmt % (line, "", line, "", ""))
    po = format.format_h % (100 * t_occ)
    pp = "" if t_perf == 0 else format.format_l % (100 * t_perf)
    pc = "" if t_cap == 0 else format.format_l % (100 * t_cap)
    print(fmt % (po, "", "total", pp, pc))


def tributary_report(states, markov, format):
    """
        generate a class-bucket occupancy report

        Args:
            states (list):          an ordered list of (state, occ) tupples
            markov (MarkovAvai):    the solution to be reported
            format (OutputFormat):  the chosen output formats

        Note:
            we treat performance and capacity as per-state fractions of nominal
    """

    fmt = format.format
    line = format.line
    print("\ntributary transitions:")
    print(fmt % ("occupancy", "state", "source", "fraction", "FITs"))
    print(fmt % (line, line, line, line, line))

    # figure out the total number of transitions into each state
    incoming = [0 for x in range(markov.numstates)]
    for i in range(markov.numstates):
        for j in range(markov.numstates):
            incoming[j] += markov.rates[i][j]

    # for each target state, list all tributary states
    for (i, occupancy) in states:
        n = markov.stateNames[i]
        po = format.format_h % (100 * occupancy)
        for (j, discard) in states:
            fits = markov.weighted[j][i]
            if fits == 0:
                continue
            src = markov.stateNames[j]
            pf = format.format_l % (100 * fits / incoming[i])
            pr = format.format_d % (fits)
            print(fmt % (po, n, src, pf, pr))
            po = ""
            n = ""


# this main routine serves two purposes:
#   a unit test case
#   sample code using the MarkovAvail class
#
if __name__ == '__main__':
    """ CLI entry point:
        process command line arguments, and process the selected files
    """

    from optparse import OptionParser

    # process the command line arguments
    umsg = "usage: %prog [options] input_file [dictionary]"
    parser = OptionParser(usage=umsg)
    parser.add_option("-d", "--debug", type="int", dest="debug",
                      default="0")
    parser.add_option("-D", "--dictionary", type="string",
                      dest="dictionary")
    (opts, files) = parser.parse_args()

    # process the model (with the dictionary)
    if len(files) < 1:
        print("ERROR: no input file specified")
    dict = files[1] if len(files) > 1 else opts.dictionary
    (m, states) = processFile(files[0], dict, opts.debug)

    # figure out how long a name has to be
    name_width = 8
    for i in range(m.numstates):
        if i in m.stateNames and len(m.stateNames[i]) > name_width:
            name_width = len(m.stateNames[i])
        if i in m.stateType and len(m.stateType[i]) > name_width:
            name_width = len(m.stateType[i])

    # generate an appropriate output format
    f = OutputFormat(name=name_width)

    # generate a set of standardreports
    state_report(states, m, f)
    class_report(m, f)
    tributary_report(states, m, f)
