"""
Test script for service modalities

Details:
Three different programs are targeting testing rates for Females 15-49.
This script demonstrates the effect of these programs under different interaction assumptions.
It can also be used as a test script, to ensure that the calculations are being done correctly.

Version: 2015dec01 by robyns
"""


print('Testing service modalities...')
from optima import Project, Program, Programset
from numpy import array

P = Project(spreadsheet='test.xlsx')

doplot = False
eps = 1e-3
testval_nested = 0.42475173
testval_random = 0.43792895
testval_additive = 0.44181250

# First set up some programs
HTC_clinics = Program(name='HTC_clinics',
              targetpars=[{'param': 'hivtest', 'pop': 'Females 15-49'}],
              targetpops=['Females 15-49'])

HTC_outreach = Program(name='HTC_outreach',
              targetpars=[{'param': 'hivtest', 'pop': 'Females 15-49'}],
              targetpops=['Females 15-49'])
               
HTC_hometest = Program(name='HTC_hometest',
              targetpars=[{'param': 'hivtest', 'pop': 'Females 15-49'}],
              targetpops=['Females 15-49'])

# What's the target population size for these programs?
targetpopsize = HTC_outreach.gettargetpopsize(t=[2013],
                                              parset=P.parsets['default'])

# Add cost-coverage function parameters to each program
HTC_clinics.costcovfn.addccopar({'t': 2013.0,
                                 'saturation':0.4,
                                 'unitcost': 40})
                         
HTC_outreach.costcovfn.addccopar({'t': 2013.0,
                                 'saturation':0.6,
                                  'unitcost': 50})
                         
HTC_hometest.costcovfn.addccopar({'t': 2013.0,
                                 'saturation':0.4,
                                  'unitcost': 20})

# Combine the 3 program together in a program set
R = Programset(programs=[HTC_clinics,HTC_outreach,HTC_hometest])

# Add parameters for the coverage-outcome functions
R.covout['hivtest']['Females 15-49'].addccopar({'intercept': 0.3,
                                                't': 2013.0,
                                                'HTC_clinics': 0.5,
                                                'HTC_outreach': 0.6,
                                                'HTC_hometest':0.1})
                    
# Define the budget and the type of interaction
budget = {'HTC_clinics': array([ 1e7,]),
          'HTC_outreach': array([ 1e6,]),
          'HTC_hometest': array([ 1e6,])}

# Plot the cost-coverage curves for each program if asked
if doplot: R.plotallcoverage(t=[2013],
                  parset=P.parsets['default'],
                  xupperlim=1e8)

# Get the coverage of each program associated with this budget
coverage = R.getprogcoverage(budget=budget,
                             t=[2013],
                             parset=P.parsets['default'],
                             proportion=True)


# Get the outcomes associated with this budget
outcomes_nested = R.getoutcomes(forwhat=budget,
                                t=[2013],
                                parset=P.parsets['default'],
                                forwhattype='budget',
                                interaction='nested')

outcomes_random = R.getoutcomes(forwhat=budget,
                                t=[2013],
                                parset=P.parsets['default'],
                                forwhattype='budget',
                                interaction='random')

outcomes_additive = R.getoutcomes(forwhat=budget,
                                t=[2013],
                                parset=P.parsets['default'],
                                forwhattype='budget',
                                interaction='additive')

r1 = 'PASS' if abs(outcomes_nested['hivtest']['Females 15-49'][0]-testval_nested)<eps else 'FAIL'
r2 = 'PASS' if abs(outcomes_random['hivtest']['Females 15-49'][0]-testval_random)<eps else 'FAIL'
r3 = 'PASS' if abs(outcomes_additive['hivtest']['Females 15-49'][0]-testval_additive)<eps else 'FAIL'

def summary():
    ''' Print out useful information'''
    output = '\n'
    output += '===================================\n'
    output += 'Calculated outcomes\n'
    output += '   Nested: %s\n'    % outcomes_nested['hivtest']['Females 15-49'][0]
    output += '   Random: %s\n'    % outcomes_random['hivtest']['Females 15-49'][0]
    output += ' Additive: %s\n'    % outcomes_additive['hivtest']['Females 15-49'][0]
    output += '===================================\n'
    output += 'Outcomes should be:\n'
    output += '   Nested: %s\n'    % testval_nested
    output += '   Random: %s\n'    % testval_random
    output += ' Additive: %s\n'    % testval_additive
    output += '===================================\n'
    output += 'Test results:\n'
    output += '   Nested: %s\n' % (r1) 
    output += '   Random: %s\n' % (r2) 
    output += ' Additive: %s\n' % (r3) 
    output += '===================================\n'
    print output

summary()

# See the effect of scaling up one of the programs
budget_outreachscaleup = {'HTC_clinics': array([ 1e7,]),
          'HTC_outreach': array([ 1e7,]),
          'HTC_hometest': array([ 1e6,])}

outcomes_nested_outreachscaleup = R.getoutcomes(forwhat=budget_outreachscaleup,
                                t=[2013],
                                parset=P.parsets['default'],
                                forwhattype='budget',
                                interaction='nested')

outcomes_random_outreachscaleup = R.getoutcomes(forwhat=budget_outreachscaleup,
                                t=[2013],
                                parset=P.parsets['default'],
                                forwhattype='budget',
                                interaction='random')

outcomes_additive_outreachscaleup = R.getoutcomes(forwhat=budget_outreachscaleup,
                                t=[2013],
                                parset=P.parsets['default'],
                                forwhattype='budget',
                                interaction='additive')

coverage_outreachscaleup = R.getprogcoverage(budget=budget_outreachscaleup,
                             t=[2013],
                             parset=P.parsets['default'],
                             proportion=True)

budget_hometestscaleup = {'HTC_clinics': array([ 1e7,]),
          'HTC_outreach': array([ 1e6,]),
          'HTC_hometest': array([ 1e7,])}

outcomes_nested_hometestscaleup = R.getoutcomes(forwhat=budget_hometestscaleup,
                                t=[2013],
                                parset=P.parsets['default'],
                                forwhattype='budget',
                                interaction='nested')

outcomes_random_hometestscaleup = R.getoutcomes(forwhat=budget_hometestscaleup,
                                t=[2013],
                                parset=P.parsets['default'],
                                forwhattype='budget',
                                interaction='random')

outcomes_additive_hometestscaleup = R.getoutcomes(forwhat=budget_hometestscaleup,
                                t=[2013],
                                parset=P.parsets['default'],
                                forwhattype='budget',
                                interaction='additive')

coverage_hometestscaleup = R.getprogcoverage(budget=budget_hometestscaleup,
                             t=[2013],
                             parset=P.parsets['default'],
                             proportion=True)

def summary_scaleup():
    ''' Print out useful information'''
    output = '\n'
    output += '===================================\n'
    output += 'Initial budget allocation:\n'
    output += ' Clinics: %s\n'    % budget['HTC_clinics'][0]
    output += ' Outreach: %s\n'    % budget['HTC_outreach'][0]
    output += ' Hometest: %s\n'    % budget['HTC_hometest'][0]
    output += 'Initial coverage:\n'
    output += ' Clinics: %s\n'    % coverage['HTC_clinics'][0]
    output += ' Outreach: %s\n'    % coverage['HTC_outreach'][0]
    output += ' Hometest: %s\n'    % coverage['HTC_hometest'][0]
    output += 'Initial outcomes:\n'
    output += '   Nested: %s\n'    % outcomes_nested['hivtest']['Females 15-49'][0]
    output += '   Random: %s\n'    % outcomes_random['hivtest']['Females 15-49'][0]
    output += ' Additive: %s\n'    % outcomes_additive['hivtest']['Females 15-49'][0]
    output += '===================================\n'
    output += 'Budget with outreach scale-up:\n'
    output += ' Clinics: %s\n'    % budget_outreachscaleup['HTC_clinics'][0]
    output += ' Outreach: %s\n'    % budget_outreachscaleup['HTC_outreach'][0]
    output += ' Hometest: %s\n'    % budget_outreachscaleup['HTC_hometest'][0]
    output += 'Coverage with outreach scale-up:\n'
    output += ' Clinics: %s\n'    % coverage_outreachscaleup['HTC_clinics'][0]
    output += ' Outreach: %s\n'    % coverage_outreachscaleup['HTC_outreach'][0]
    output += ' Hometest: %s\n'    % coverage_outreachscaleup['HTC_hometest'][0]
    output += 'Outcomes with outreach scale-up:\n'
    output += '   Nested: %s\n'    % outcomes_nested_outreachscaleup['hivtest']['Females 15-49'][0]
    output += '   Random: %s\n'    % outcomes_random_outreachscaleup['hivtest']['Females 15-49'][0]
    output += ' Additive: %s\n'    % outcomes_additive_outreachscaleup['hivtest']['Females 15-49'][0]
    output += '===================================\n'
    output += 'Budget with hometest scale-up:\n'
    output += ' Clinics: %s\n'    % budget_hometestscaleup['HTC_clinics'][0]
    output += ' Outreach: %s\n'    % budget_hometestscaleup['HTC_outreach'][0]
    output += ' Hometest: %s\n'    % budget_hometestscaleup['HTC_hometest'][0]
    output += 'Coverage with hometest scale-up:\n'
    output += ' Clinics: %s\n'    % coverage_hometestscaleup['HTC_clinics'][0]
    output += ' Outreach: %s\n'    % coverage_hometestscaleup['HTC_outreach'][0]
    output += ' Hometest: %s\n'    % coverage_hometestscaleup['HTC_hometest'][0]
    output += 'Outcomes with hometest scale-up:\n'
    output += '   Nested: %s\n' % outcomes_nested_hometestscaleup['hivtest']['Females 15-49'][0]
    output += '   Random: %s\n' % outcomes_random_hometestscaleup['hivtest']['Females 15-49'][0]
    output += ' Additive: %s\n' % outcomes_additive_hometestscaleup['hivtest']['Females 15-49'][0]
    output += '===================================\n'
    print output

summary_scaleup()

