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

I defined additional (edge) properties for specifying transition rates

	edge.fits ...	a transition rate in FITs
	edge.rate ...	a transition rate in FITs

	edge.time ...	a frequency/processing interval, followed by a letter
			indicating the unit (seconds, minutes, hours, days,
			weeks, years).

	If no transition rate property is found, it will look up the edge
	label in an external dictionary to find the associated rate.

I then implemented a new python class (MarkovAvailability) that processes an
extended directed graph description, normalizes the transition rates to FITs,
generates the associated set of simultaneous linear equations, solves them,
and extracts the state occupancies.

I also defined new properties for nodes:

	node.state 	... a string that can be used to put the state into
			a general class of buckets (e.g. "up", "down")
	node.performance ... a string that can be used to characterize the
			performance associated with this state.
	node.capacity ... a string that can be used to characterize the
			system capacity associated with this state.

	These propserties are not actually used in by the Markov Model,
	but they are parsed and exposed to the client, to permit more
	interesting reporting.

MarkovAvail.py also includes

	a processFile method that parses a dot graph and data dictionary,
	uses them to instantiate and solve a MarkovAvail, and generates a
	more convenient (sorted by occupancy) list of solutions.

MarkovTest.py includes

	a main method that processes parameters, invokes processFile, and
	then uses the returned solution to generate a series of sample 
	reports.
		
	routines to generate per-state and per-class reports from the
	solved Markov Model

	this application uses node attributes as:

		aggregates results into buckets based on node.state

		treats node.performance as a fraction and reports on
		the occupancy-weighted performance, both by state 
		and by availability bucket

		treats node.capacity as a fraction and reports on
		the occupancy-weighted capacity, both by state 
		and by availability bucket

	these can be used as sample "how to" code, but they also turn 
	the MarkovAvail class into a reasonble CLI


Files:
	MarkovAvail.py	the Markov Availability model solution class
	MarkovTest.py	a sample application using the MarkovAvail class
	Tires		a sample availability model
	Tires.dict	an external data dictionary for transition rates

#### PROBLEM ###
	In 2024 I updated MarkovAvail.py to use pydotplus and be more python3.
		./MarkovTest.py Complex Complex.dict	... seems to work
		./MarkovTest.py Tires Tires.dict	... now fails

		It dies on a numpy.linalg.LinAlgError:Singular Matrix
		I spent a little while looking at it

			./MarkovTest.py -d2 Tires Tires.dict

		and the problem was not obvious (to me).  My wild guess
		is that a new implementation of numpy matrix inversion
		does new tests that this matrix now fails.  If I ever
		want to use this again, I should spend a while getting
		deeper into what numpy doesn't like about my matrix and
		why my matrix looks like that.
