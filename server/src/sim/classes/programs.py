import uuid
from operator import mul
class Program:
	def __init__(self,name):
		self.name = name
		self.uuid = uuid.uuid4()

		self.modalities = []
		self.metamodalities = [] # One metamodality for every combination of modalities, including single modalities
		self.effective_coverage = [] # An effective coverage for every metamodality

		self.reachability_interaction = 'random' # These are the options on slide 7 of the proposal
		# The reachability interaction enables the metamodality maxcoverage to be automatically set

	def calculate_effective_coverage(self,spending):
		# These are the shaded areas in the target population plots
		assert(len(spending)==len(self.modalities))

		coverage = []
		for i in xrange(0,len(spending)):
			coverage.append(self.modalities[i].get_coverage(spending[i]))


		self.effective_coverage = []
		for m in self.metamodalities:
			effective_coverage.append(m.get_coverage(self.modalities,coverage))





			for i in xrange(0,len(self.metamodalities)):
				coverages = []
				for j in xrange(0,len(self.metamodalities[i])):
					coverages.append()
				self.effective_coverage

	def add_modality(self,name):
		new_modality = Modality(name)
		self.modalities.append(new_modality)
		# Synchronize metamodalities
		# Add a new metamodality with all of the previous ones
		current_metamodalities = len(self.metamodalities)
		for i in xrange(0,len(current_metamodalities)):
			self.metamodalities.append(Metamodality(new_modality,metamodality=self.metamodalities[i]))
		self.metamodalities.append()

	def remove_modality(self,name,uuid):
		idx = 1 # Actually look up the modality by name or by uuid
		m = self.modalities.pop(idx)


	def reflow_metamodalities(self):
		# This function goes through and calculates the metamodality maxcoverage
		# and enforces no double counting (when reachability interaction is not additive)
		if self.reachability_interaction == 'random':
			# Random reachability means that if modality 1 is capable of reaching 40/100 people, and 
			# modality 2 is capable of reaching 20/100 people, then the probability of one person being reached
			# by both programs is (40/100)*(20/100)
			modality_coverage = [m.maxcoverage for m in self.modalities] # The maximum coverage for each modality
			# Now go through the metamodalities
			


class Metamodality:
	# The metamodality knows the coverage (number of people) who fall into the overlapping category
	# The amount of overlap still needs to be specified though
	# For example, if the population size is 100 people, and modality 1 reaches 40, and modality 2 reaches 20,
	# and the metamodality reaches 10, then we know that 10 people are reached by both - 50% of modality 2, and 25% of modality 1
	# So the metamodality coverage is a fraction of the total population
	# And it must be smaller than the smallest coverage for the individual modalities
	def __init__(self,modalities,method='maximum',metamodality=None,overlap=None): # where m1 and m2 are Modality instances
		self.modalities = [m.uuid for m in modalities]
		self.maxcoverage = min([m.maxcoverage for m in modalities]) # Default upper bound on fractional coverage of the total population
		


		if metamodality is not None:
			self.modalities += metamodality.modalities # Append the UUIDs from the previous metamodality object

		# We do not store weakrefs here because conversion from class to dict
		# may be frequent here, and it could become expensive if the references
		# are regenerated too frequently

		self.method = method

	def get_outcome(self,modalities,effective_coverage):
		outcomes = []
		for m in modalities:
			if m.uuid in self.modalities:
				outcomes.append(m.get_coverage(effective_coverage))

		# The method controls how the effective coverage from each contributing
		# modality is combined
		if self.method == 'maximum':
			return max(outcomes)

	def get_coverage(self,modalities,coverage):
		# Return a list of all of the coverages corresponding to the modalities
		# referred to by this metamodality instance
		# There is one coverage for each modality

		# Note that internally, the coverages are divided equally
		# For example, if the population size is 100 people, and modality 1 is capable of reaching 40, and modality 2 is capable of reaching 20,
		# and the metamodality reaches 10, then we know that 10 people are reached by both. So we set the metamodality maxcoverage
		# to 10 people (0.1). 
		# Now, suppose modality 1 reaches 20 people, and modality 2 reaches 20 people. This mean that of the metamodality now reaches 5 people
		# So we have
		# metamodalitycoverage = (m_1_actualcoverage/m_1_max*m_2_actualcoverage/m_2_max)*self.maxcoverage
		# is the fraction of the total population reached by this combination of programs
		actual_coverage = self.maxcoverage
		for i in xrange(0,len(modalities)):
			if modalities[i].uuid in self.modalities:
				actual_coverage *= coverage[i]/modalities[i].maxcoverage
		return actual_coverage

class Modality:
	def __init__(self,name):
		self.name = name

		self.maxcoverage = 1 # The maximum fraction of the total population that this modality can reach

		# The number of people reached by this program is self.get_coverage(spending)*self.maxcoverage*population_size

		self.population = 'FSW' # Target population, must be present in the region
		self.parameter = 'testing' # Target parameter, must already exist in region metadata

		# Cost-Coverage
		self.ccfun = linear
		self.ccparams['function'] = 'linear' # Use this dictionary to load/save
		self.ccparams['parameters'] = [1 0]
		
		# Coverage-outcome
		self.cofun = linear
		self.coparams['function'] = 'linear' # Use this dictionary to load/save
		self.coparams['parameters'] = [1 0]

		self.uuid = uuid.uuid4()

	def get_coverage(self,spending):
		# self.ccparams['function'] is one of the keys in self.ccfun
		# self.ccparams['parameters'] contains whatever is required by the curve function
		return self.ccfun(self.ccparams['parameters'],spending)

	def getoutcome(self,effective_coverage):
		return self.cofun(self.coparams['parameters'],effective_coverage)

def linear(params,x):
	return params[0]*x+params[1]

def sigmoid(params,x):
	return params[0]/exp((params[1]*(x-params[2])/params[3]))
