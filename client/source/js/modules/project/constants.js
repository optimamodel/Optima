define(['./module'], function (module) {
  'use strict';

  var DEFAULT_POPULATIONS = [
    {
      active: false, internal_name: "FSW", short_name: "FSW", name: "Female sex workers",
      hetero: true, homo: false, injects: false, sexworker: true, client: false, female: true, male: false
    },
    {
      active: false, internal_name: "CSW", short_name: "Clients", name: "Clients of sex workers",
      hetero: true, homo: false, injects: false, sexworker: false, client: true, female: false, male: true
    },
    {
      active: false, internal_name: "MSM", short_name: "MSM", name: "Men who have sex with men",
      hetero: false, homo: true, injects: false, sexworker: false, client: false, female: false, male: true
    },
    {
      active: false, internal_name: "TI", short_name: "Transgender", name: "Transgender individuals",
      hetero: false, homo: true, injects: false, sexworker: false, client: false, female: false, male: false
    },
    {
      active: false, internal_name: "PWID", short_name: "PWID", name: "People who inject drugs",
      hetero: true, homo: false, injects: true, sexworker: false, client: false, female: false, male: false
    },
    {
      active: false, internal_name: "MWID", short_name: "Male PWID", name: "Males who inject drugs",
      hetero: true, homo: false, injects: true, sexworker: false, client: false, female: false, male: true
    },
    {
      active: false, internal_name: "FWID", short_name: "Female PWID", name: "Females who inject drugs",
      hetero: true, homo: false, injects: true, sexworker: false, client: false, female: true, male: false
    },
    {
      active: false, internal_name: "CHILD", short_name: "Children", name: "Children (2-15)",
      hetero: false, homo: false, injects: false, sexworker: false, client: false, female: false, male: false
    },
    {
      active: false, internal_name: "INF", short_name: "Infants", name: "Infants (0-2)",
      hetero: false, homo: false, injects: false, sexworker: false, client: false, female: false, male: false
    },
    {
      active: false, internal_name: "OM15_49", short_name: "Males 15-49", name: "Other males (15-49)",
      hetero: true, homo: false, injects: false, sexworker: false, client: false, female: false, male: true
    },
    {
      active: false, internal_name: "OF15_49", short_name: "Females 15-49", name: "Other females (15-49)",
      hetero: true, homo: false, injects: false, sexworker: false, client: false, female: true, male: false
    },
    {
      active: false, internal_name: "OM", short_name: "Other males", name: "Other males [enter age]",
      hetero: true, homo: false, injects: false, sexworker: false, client: false, female: false, male: true
    },
    {
      active: false, internal_name: "OF", short_name: "Other females", name: "Other females [enter age]",
      hetero: true, homo: false, injects: false, sexworker: false, client: false, female: true, male: false
    }
  ];

  var DEFAULT_PROGRAMS = [
    {
      active: false, internal_name: "COND", short_name: "Condoms",
      name: "Condom promotion and distribution", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Condom usage probability, regular partnerships',
          value: { 'signature': ['condom', 'reg'], 'progs': [] }
        },
        {
          active: true,
          name: ' Condom usage probability, casual partnerships',
          value: { 'signature': ['condom', 'cas'], 'progs': [] }
        }
      ]
    },
    {
      active: false, internal_name: "SBCC", short_name: "SBCC",
      name: "Social and behavior change communication", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Condom usage probability, regular partnerships',
          value: { 'signature': ['condom', 'reg'], 'progs': [] }
        },
        {
          active: true,
          name: ' Condom usage probability, casual partnerships',
          value: { 'signature': ['condom', 'cas'], 'progs': [] }
        }
      ]
    },
    {
      active: false, internal_name: "STI", short_name: "STI",
      name: "Diagnosis and treatment of sexually transmitted infections", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Discharging STI prevalence',
          value: {'signature': ['stiprevdis'], 'progs': []}
        },
        {
          active: true,
          name: 'Ulcerative STI prevalence',
          value: {'signature': ['stiprevulc'], 'progs': []}
        }
      ]
    },
    {
      active: false, internal_name: "VMMC", short_name: "VMMC",
      name: "Voluntary medical male circumcision", saturating: false,
      parameters: [
        {
          active: true,
          name: 'Number of circumcisions performed per year',
          value: {'signature': ['numcircum'], 'progs': []}
        }
      ]
    },
    {
      active: false, internal_name: "CT", short_name: "Cash transfers",
      name: "Cash transfers for HIV risk reduction", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Number of acts per person per year, regular',
          value: {'signature': ['numacts', 'reg'], 'progs': []}
        },
        {
          active: true,
          name: 'Number of acts per person per year, casual',
          value: {'signature': ['numacts', 'cas'], 'progs': []}
        }
      ]
    },
    {
      active: false, internal_name: "FSWP", short_name: "FSW programs",
      name: "Programs for female sex workers and clients", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Condom usage probability, commercial partnerships',
          value: { 'signature': ['condom', 'com'], 'progs': ['FSW'] }
        },
        {
          active: true,
          name: 'Condom usage probability, commercial partnerships',
          value: { 'signature': ['condom', 'com'], 'progs': ['CSW'] }
        },
        {
          active: true,
          name: 'HIV testing rates',
          value: { 'signature': ['hivtest'], 'progs': ['FSW'] }
        }
      ]
    },
    {
      active: false, internal_name: "MSMP", short_name: "MSM programs",
      name: "Programs for men who have sex with men", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Condom usage probability, regular partnerships',
          value: {'signature': ['condom', 'reg'], 'progs': ['MSM']}
        },
        {
          active: true,
          name: 'Condom usage probability, casual partnerships',
          value: {'signature': ['condom', 'cas'], 'progs': ['MSM']}
        }
      ]
    },
    {
      active: false, internal_name: "PWIDP", short_name: "PWID programs",
      name: "Programs for people who inject drugs", saturating: true,
      parameters: [
        {
          active: true,
          name: 'HIV testing rates',
          value: {'signature': ['hivtest'], progs: ['hivtest']}
        },
        {
          active: true,
          name: 'Condom usage probability, regular partnerships',
          value: {'signature': ['condom', 'reg'], progs: ['PWID']}
        },
        {
          active: true,
          name: 'Condom usage probability, casual partnerships',
          value: {'signature': ['condom', 'cas'], progs: ['PWID']}
        }
      ]

    },
    {
      active: false, internal_name: "OST", short_name: "OST",
      name: "Opiate substitution therapy", saturating: false,
      parameters: [
        {
          active: true,
          name: 'Number of people on OST',
          value: {'signature': ['numost'], 'progs': []}
        }
      ]

    },
    {
      active: false, internal_name: "NSP", short_name: "NSP",
      name: "Needle-syringe program", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Needle-syringe sharing rate',
          value: {'signature': ['sharing'], 'progs': []}
        }
      ]

    },
    {
      active: false, internal_name: "PREP", short_name: "PrEP",
      name: "Pre-exposure prophylaxis/microbicides", saturating: true,
      parameters: [
        {
          active: true,
          name: 'PrEP prevalence',
          value: {'signature': ['prep'], 'progs': []}
        }
      ]

    },
    {
      active: false, internal_name: "PEP", short_name: "PEP",
      name: "Post-exposure prophylaxis", saturating: true,
      parameters: [
        {
          active: true,
          name: 'PEP prevalence',
          value: {'signature': ['pep'], 'progs': []}
        }
      ]

    },
    {
      active: false, internal_name: "HTC", short_name: "HTC",
      name: "HIV testing and counseling", saturating: true,
      parameters: [
        {
          active: true,
          name: 'HIV testing rates',
          value: {'signature': ['hivtest'], 'progs': []}
        }
      ]

    },
    {
      active: false, internal_name: "ART", short_name: "ART",
      name: "Antiretroviral therapy", saturating: false,
      parameters: [
        {
          active: true,
          name: 'Number of people on 1st-line treatment',
          value: {'signature': ['tx1'], 'progs': []}
        },
        {
          active: true,
          name: 'Number of people on 2nd-line treatment',
          value: {'signature': ['tx2'], 'progs': []}
        }
      ]

    },
    {
      active: false, internal_name: "PMTCT", short_name: "PMTCT",
      name: "Prevention of mother-to-child transmission", saturating: false,
      parameters: [
        {
          active: true,
          name: 'Number of women on PMTCT',
          value: {'signature': ['numpmtct'], 'progs': []}
        }
      ]
    },
    {
      active: false, internal_name: "CARE", short_name: "Other care",
      name: "Other HIV care", saturating: false
    },
    {
      active: false, internal_name: "OVC", short_name: "OVC",
      name: "Orphans and vulnerable children", saturating: false
    },
    {
      active: false, internal_name: "MGMT", short_name: "MGMT",
      name: "Management", saturating: false
    },
    {
      active: false, internal_name: "HR", short_name: "HR",
      name: "HR and training", saturating: false
    },
    {
      active: false, internal_name: "ENV", short_name: "ENV",
      name: "Enabling environment", saturating: false
    },
    {
      active: false, internal_name: "SP", short_name: "SP",
      name: "Social protection", saturating: false
    },
    {
      active: false, internal_name: "MESR", short_name: "M&E",
      name: "Monitoring, evaluation, surveillance, and research", saturating: false
    },
    {
      active: false, internal_name: "INFR", short_name: "INFR",
      name: "Health infrastructure", saturating: false
    }
  ];

  return module.constant('DEFAULT_PROGRAMS', DEFAULT_PROGRAMS)
    .constant('DEFAULT_POPULATIONS', DEFAULT_POPULATIONS);

});
