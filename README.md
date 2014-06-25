MarkovAvailability
=================
Tools for building and solving steady state Markov Availability models

In the past I have used white-boards to develop Markov Availability models
and spreadhsheets to solve them ... and I did not like interacting with the
models.  I decided I wanted a tool chain with:

	an intuitive and easily edited input format
		where nodes could be decorated with availability state info
		where edges could be decorated with transition rate info

	the ability to generate and solve equations for state occupancy

	producing output including
		suitable-for-publication state model graphics
		the occupancy of each model state
		the occupancy of each class of states
		statistical breakdown of the tributaries to each state

I decided to start with the representation.  And a little searching turned up the 
graphviz dot language for representing directed graphs.  The dot input language
allows nodes and edges to be decorated with arbitrary attributes, giving me the
ability to represent additional information.

I also needed the ability to process those input files.  I quickly found the pydot
package for parsing dot graph descriptions and operating on the resulting graphs.

I defined additional properties for dot graphs:

	node.state ...	the name of a state occupancy aggregation bucket.  One
			might, for example, say "state=up" for all states that
			should be considered to be "up".  There can be arbitrarily
			many such buckets, and the only effect they have is in
			the summary report.

	edge.fits ...	a transition rate in FITs
	edge.rate ...	a transition rate in FITs

	edge.time ...	a frequency/processing interval, followed by a letter
			indicating the unit (seconds, minutes, hours, days,
			weeks, years).

I then implemented a new python class (MarkovAvailability) that processes an
extended directed graph description, normalizes the transition rates to FITs,
generates the associated set of simultaneous linear equations, solves them,
and extracts the state occupancies.

The module also includes a main routine, to process a file and generate a report.
The main also serves as an example of how the MarkovAvail class can be used by a program.

	Files:
		MarkovAvail.py	the Markov Availability model solution class
		Tires		a sample availability model
		Tires.dict	an external data dictionary for transition rates
