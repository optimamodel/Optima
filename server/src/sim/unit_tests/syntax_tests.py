# This script just runs various commands to ensure that the syntax isn't broken
# and that commands run to completion without fatal errors
# Tests in here perform minimal, if any, validation of variable values

import sys
sys.path.append('..')
import optima
from liboptima.utils import dict_equal
import unittest
import numpy


class TestSyntax(unittest.TestCase):

	def test_portfolio_save_load(self):
		r1 = optima.Project.load_json('../projects/Dedza.json')
		r2 = optima.Project.load_json('../projects/Dowa.json')
		tempsimbox1 = r1.createsimbox('GPA1', isopt = True, createdefault = True)
		tempsimbox2 = r2.createsimbox('GPA2', isopt = True, createdefault = True)
		
		p1 = optima.Portfolio('test')
		p1.appendproject(r1)
		p1.appendproject(r2)
		p1.gpalist = [tempsimbox1,tempsimbox2]
		print p1.gpalist
		p1.save('cache.bin')
		p2 = optima.Portfolio.load('cache.bin')
		print p2.gpalist

	def test_saving_and_loading(self):
		r = optima.Project.load_json('../projects/Dedza.json') # Load old style JSON
		r.save_json('../projects/Dedza_newstyle.json')
		r2 = optima.Project.load_json('../projects/Dedza_newstyle.json') # Load new style JSON
		r2.createsimbox('Simbox 1')
		r2.simboxlist[0].createsim('sim1')
		r2.runsimbox(r2.simboxlist[0])
		r2.save('../projects/Dedza_newstyle_withsim.bin')
		r3 = optima.Project.load('../projects/Dedza_newstyle_withsim.bin') # Load new style JSON
		print r
		print r3
		print r3.simboxlist[0].simlist[0].processed

	def test_saving_and_loading_binary(self):
		r = optima.Project.load_json('../projects/Dedza.json') # Load old style JSON
		r.save('../projects/Dedza_newstyle.bin')
		r2 = optima.Project.load('../projects/Dedza_newstyle.bin') # Load new style JSON
		r2.createsimbox('Simbox 1')
		r2.simboxlist[0].createsim('sim1')
		r2.runsimbox(r2.simboxlist[0])
		r2.save('../projects/Dedza_newstyle_withsim.bin')
		r3 = optima.Project.load('../projects/Dedza_newstyle_withsim.bin') # Load new style JSON
		print r
		print r3
		print r3.simboxlist[0].simlist[0].processed

		# Test sim.viewuncerresults
		r3.simboxlist[0].simlist[0].plotresults(show_wait=False)

		# Test simbox.viewmultiresults
		r3.simboxlist[0].createsim('sim2') # This should really be r.simboxlist.createsim('sim_name') ...
		r3.runsimbox(r3.simboxlist[0])
		r3.simboxlist[0].viewmultiresults(show_wait=False)

	# def test_from_xlsx(self):
	# 	# Test running a simulation from XLSX
	# 	r = project.Project('Haiti (from XLSX)',defaults.haiti['populations'],defaults.haiti['programs'],defaults.haiti['datastart'],defaults.haiti['dataend'])
	# 	r.makeworkbook('../projects/Haiti_Test.xlsx') # Write to a dummy file for test purposes
	# 	r.loadworkbook('../projects/Haiti.xlsx')
	# 	r.createsimbox('Simbox 1')
	# 	r.simboxlist[0].createsim('sim1') # This is really confusing....
	# 	r.runsimbox(r.simboxlist[0])

	

if __name__ == '__main__':
    unittest.main()