#!/usr/bin/python
#
#   This takes a basic system configuration and time/rate parameters,
#   computes the implied state transition rates, and generates a
#   dictionary of edge names and rates that will be used to solve
#   a Markov model.
#
#   For complex systems, the transition rates are seldom simple values,
#   and the dictionary language implemented in MarkovAvail.py does not
#   support variables and expressions.  I felt the easiest way to add
#   that capability was to write a program in python (that does support
#   variables and expressions) to generate the values.
#
#   The computations are highly model dependent, but the code to output
#   them should be totally generic
#

# time constants
HOUR = 1
MINUTE = float(HOUR) / 60
SECOND = float(MINUTE) / 60
DAY = 24 * HOUR
WEEK = 7 * DAY
YEAR = 365.25 * DAY

def fits(time):
    """ convert a time to a FIT rate """
    return(1000000000 / float(time))

# system configuration parameters
NIC_PER_IOM = 2             # NICs per I/O Module
NUM_IOM = 6                 # I/O modules
NUM_SCM = 6                 # Storage Class Memory modules
NUM_SSD = 6                 # Solid State Disk modules
NUM_CTLR = 2                # controllers
NUM_SWITCH = 4              # interconnects

NUM_FAN = 4                 # fans
NUM_POWER = 2               # power supplies

# failure rates
FIT_POWER = 1642            # typical
FIT_FAN = 618               # typical
FIT_CTLR = 4000             # typical
FIT_SWITCH = 40             # typical

FIT_NIC = 200               # typical
FIT_IOM_SWITCH = 40         # typical

FIT_SCM_FPGA = 20           # typical
FIT_SCM_SWITCH = 40         # typical
FIT_SSD_SWITCH = 40         # typical

FIT_SW = fits(4 * YEAR)     # fantsy ... single system crashes
F_SW_BOTH = 0.05            # fantsy ... fraction that take down both
F_SW_HARD = 0.01            # fantsy ... fraction that don't recover

# automatic recovery times
SOFT_REBOOT = 60 * SECOND   # worst case ... one system, warm-start
HARD_REBOOT = 120 * SECOND  # worst case ... two system, cold start

# service/response times
EMERG_SW = 24 * HOUR        # fantasy ... what fraction are hard to diagnose?
EMERG_SSD = 12 * HOUR       # specified
EMERG_BOARD = 6 * HOUR      # specified
SCHED_BOARD = 24 * HOUR     # specified
SCHED_MODULE = 24 * HOUR    # specified

values = {}
descrs = {}

# definitions of failure and recoveryrates
descrs["6*IOM_fail"] = "failure rate for (any part of) an any IOM card"
descrs["5*IOM_fail"] = "second IOM failure rate"
descrs["6*SCM_fail"] = "failure rate for (any part of) an any SCM card"
descrs["5*SCM_fail"] = "second SCM failure rate"
descrs["6*SSD_fail"] = "failure rate for (any part of) any SSD card"
descrs["5*SSD_fail"] = "second SSD failure rate"
descrs["4*switch_fail"] = "failure rate for any large cross controller switches"
descrs["3*switch_fail"] = "failure rate for second cross controller switches"
descrs["2*ctlr_fail"] = "failure rate for (any) controller board hardware"
descrs["1*ctlr_fail"] = "failure rate for second controller board hardware"
descrs["4*fan_fail"] = "first fan failure rate"
descrs["3*fan_fail"] = "second fan failure rate"
descrs["2*PS_fail"] = "first power supply failure rate"
descrs["1*PS_fail"] = "second power supply failure rate"
descrs["2*s/w_fail"] = "failure rate for (any) controller software"
descrs["s/w_fail2"] = "failure rate for s/w on second controller"
descrs["2*s/w_hard"] = "rate of unrecoverable single controller failures"
descrs["1*s/w_hard"] = "rate of second unrecoverable single controller failures"
descrs["2*s/w_double"] = "s/w falures that take down all controllers"
descrs["2*s/w_double_hard"] = "rate of unrecoverable s/w failures that take both controllers down"

descrs["s/w_restart"] = "controller software soft restart rate"
descrs["s/w_reboot"] = "controller software hard restart rate"
descrs["rplc_module"] = "rate for (non-emergency) module replacement"
descrs["rplc_board"] = "rate for (non-emergency) board replacement"
descrs["emergency_h/w"] = "rate for (emergency) board replacement"
descrs["emergency_s/w"] = "rate to (emergency) diagnose and fix a hard s/w failure"
descrs["rplc_SSD"] = "rate to (emergency) remove, repopulate and replace an SSD board"

# computations of failure and recovery rates
values["6*IOM_fail"] = NUM_IOM * (FIT_IOM_SWITCH + (NIC_PER_IOM * FIT_NIC))
values["5*IOM_fail"] = (NUM_IOM - 1) * (FIT_IOM_SWITCH + (NIC_PER_IOM * FIT_NIC))
values["6*SCM_fail"] = NUM_SCM * (FIT_SCM_SWITCH + FIT_SCM_FPGA)
values["5*SCM_fail"] = (NUM_SCM - 1) * (FIT_SCM_SWITCH + FIT_SCM_FPGA)
values["6*SSD_fail"] = NUM_SSD * FIT_SSD_SWITCH
values["5*SSD_fail"] = (NUM_SSD - 1) * FIT_SSD_SWITCH
values["4*switch_fail"] = NUM_SWITCH * FIT_SWITCH
values["3*switch_fail"] = (NUM_SWITCH - 1) * FIT_SWITCH
values["2*ctlr_fail"] = NUM_CTLR * FIT_CTLR
values["1*ctlr_fail"] = (NUM_CTLR - 1) * FIT_CTLR
values["4*fan_fail"] = NUM_FAN * FIT_FAN
values["3*fan_fail"] = (NUM_FAN - 1) * FIT_FAN
values["2*PS_fail"] = NUM_POWER * FIT_POWER
values["1*PS_fail"] = (NUM_POWER - 1) * FIT_POWER
values["2*s/w_fail"] = NUM_CTLR * FIT_SW
values["1*s/w_fail"] = ((NUM_CTLR - 1) * FIT_SW)
values["2*s/w_double"] = NUM_CTLR * FIT_SW * F_SW_BOTH
values["2*s/w_hard"] = NUM_CTLR * FIT_SW * F_SW_HARD
values["1*s/w_hard"] = (NUM_CTLR - 1) * FIT_SW * F_SW_HARD
values["2*s/w_double_hard"] = NUM_CTLR * FIT_SW * F_SW_HARD * F_SW_BOTH

values["s/w_restart"] = fits(SOFT_REBOOT)
values["s/w_reboot"] = fits(HARD_REBOOT)
values["rplc_module"] = fits(SCHED_MODULE)
values["rplc_board"] = fits(SCHED_BOARD)
values["emergency_h/w"] = fits(EMERG_BOARD)
values["emergency_s/w"] = fits(EMERG_SW)
values["rplc_SSD"] = fits(EMERG_SSD)

#
# Note:
#   The (preceding) value computations are entirely model-dependent.
#   The (following) code that outputs them is model-independent
#
import datetime
import sys

if __name__ == '__main__':

    # figure out our input file and print a disclaimer
    filename = None
    for arg in sys.argv:
        if filename is None:
            filename = arg

    # figure out what time it is
    now = datetime.datetime.now()
    when = "%d/%02d/%04d" % (now.month, now.day, now.year)
    when += " %02d:%02d:%02d" % (now.hour, now.minute, now.second)

    # stick a where I came from header on the output
    print("#")
    print("# rate values generated %s by %s" % (when, filename))
    print("#")

    # figure out how wide to make our output fields
    WID_VALUE = 16      # one billion seconds
    wid_name = 8        # with of parameter names
    for k in values:
        if len(k) > wid_name:
            wid_name = len(k)
    h_format = "# %%-%ds\t%%%ds" % (wid_name, WID_VALUE)
    d_format = "%%-%ds\t%%%dd\t# %%s" % (wid_name, WID_VALUE)

    # print out the values
    print(h_format % ("parameter", "FITs"))
    print(h_format % ("---------", "-----"))
    for k in sorted(values):
        d = descrs[k] if k in descrs else ""
        print(d_format % (k, values[k], d))
