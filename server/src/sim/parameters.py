ALL_PARAMETERS_SOURCE = \
"""
Parameter name;Example sheet & row;Description;Notes;
M.aidstest;='Testing & Treatment'!W14;AIDS testing rate per person per year;
M.circum[:];='Sexual behavior'!W69:W74;Circumcision probability;
M.condom.cas[:];='Sexual behavior'!W47:W52;Condom usage probability, casual partnerships;
M.condom.com[:];='Sexual behavior'!W58:W63;Condom usage probability, commercial partnerships;
M.condom.reg[:];='Sexual behavior'!W36:W41;Condom usage probability, regular partnerships;
M.const.cd4trans.acute;='Constants'!C15;Relative HIV transmissibility, acute stage;
M.const.cd4trans.aids;='Constants'!C19;Relative HIV transmissibility, AIDS stage;
M.const.cd4trans.gt200;='Constants'!C18;Relative HIV transmissibility, CD4>200 stage;
M.const.cd4trans.gt350;='Constants'!C17;Relative HIV transmissibility, CD4>350 stage;
M.const.cd4trans.gt500;='Constants'!C16;Relative HIV transmissibility, CD4>500 stage;
M.const.death.acute;='Constants'!C49;HIV-related mortality rate, acute stage;
M.const.death.aids;='Constants'!C53;HIV-related mortality rate, acute stage;
M.const.death.gt200;='Constants'!C52;HIV-related mortality rate, CD4>200 stage;
M.const.death.gt350;='Constants'!C51;HIV-related mortality rate, CD4>350 stage;
M.const.death.gt500;='Constants'!C50;HIV-related mortality rate, CD4>500 stage;
M.const.death.tb;='Constants'!C55;TB-related mortality rate;
M.const.death.treat;='Constants'!C54;Mortality rate while on treatment;
M.const.eff.circ;='Constants'!C62;Per-act efficacy of circumcision;
M.const.eff.condom;='Constants'!C61;Per-act efficacy of condoms;
M.const.eff.dx;='Constants'!C63;Diagnosis-related behavior change efficacy;
M.const.eff.ost;='Constants'!C65;Sharing rate reduction from methadone;
M.const.eff.pmtct;='Constants'!C66;Per-birth efficacy of PMTCT;
M.const.eff.sti;='Constants'!C64;STI-related transmission increase;
M.const.eff.tx;='Constants'!C67;Treatment-related transmission decrease;
M.const.fail.first;='Constants'!C42;First-line ART failure rate;
M.const.fail.second;='Constants'!C43;Second-line ART failure rate;
M.const.prog.acute;='Constants'!C25;Progression rate from acute to CD4>500 stage;
M.const.prog.gt200;='Constants'!C28;Progression rate from CD4>200 to AIDS stage;
M.const.prog.gt350;='Constants'!C27;Progression rate from CD4>350 to CD4>200 stage;
M.const.prog.gt500;='Constants'!C26;Progression rate from CD4>500 to CD4>350 stage;
M.const.recov.gt200;='Constants'!C36;Treatment recovery rate from AIDS to CD4>200 stage;
M.const.recov.gt350;='Constants'!C35;Treatment recovery rate from CD4>200 to CD4>350 stage;
M.const.recov.gt500;='Constants'!C34;Treatment recovery rate from CD4>350 to CD4>500 stage;
M.const.trans.inj;='Constants'!C7;Absolute per-act transmissibility of injection;
M.const.trans.mfi;='Constants'!C3;Absolute per-act transmissibility of male-female insertive intercourse;
M.const.trans.mfr;='Constants'!C4;Absolute per-act transmissibility of male-female receptive intercourse;
M.const.trans.mmi;='Constants'!C5;Absolute per-act transmissibility of male-male insertive intercourse;
M.const.trans.mmr;='Constants'!C6;Absolute per-act transmissibility of male-male receptive intercourse;
M.const.trans.mtctbreast;='Constants'!C8;Absolute per-child transmissibility with breastfeeding;
M.const.trans.mtctnobreast;='Constants'!C9;Absolute per-child transmissibility without breastfeeding;
M.death[:];='Other epidemiology'!W3:W8;Background death rates;
M.hivtest[:];='Testing & Treatment'!W3:W8;HIV testing rates;
M.numacts.cas[:];='Sexual behavior'!W14:W19;Number of acts per person per year, casual;
M.numacts.com[:];='Sexual behavior'!W25:W30;Number of acts per person per year, commercial;
M.numacts.inj[:];='Injecting behavior'!W3:W8;Number of injections per person per year;
M.numacts.reg[:];='Sexual behavior'!W3:W8;Number of acts per person per year, regular;
M.numcircum;='Sexual behavior'!W80:W85;Number of circumcisions performed per year;
M.numost;='Injecting behavior'!W20;Number of people on OST;
M.numpmtct;='Testing & Treatment'!W54;Number of women on PMTCT;
M.popsize[:];Not modifiable;Total population size;
M.pep;='Testing & Treatment'!W43:W48;PEP prevalence;
M.prep;='Testing & Treatment'!W32:W37;PrEP prevalence;
M.sharing;='Injecting behavior'!W14;Needle-syringe sharing rate;
M.stiprevdis[:];='Other epidemiology'!W25:W30;Discharging STI prevalence;
M.stiprevulc[:];='Other epidemiology'!W14:W19;Ulcerative STI prevalence;
M.tx1;='Testing & Treatment'!W20;Number of people on 1st-line treatment;
M.tx2;='Testing & Treatment'!W26;Number of people on 2nd-line treatment;
"""

def parameters():
    lines = [l.strip() for l in ALL_PARAMETERS_SOURCE.split('\n')][2:-1]
    split_lines = [l.split(';') for l in lines]
    return [{'keys':r[0].replace('[:]','').split('.')[1:],'name':r[2]} for r in split_lines]

def parameter_name(params, key):
    if not type(key)==list: key=[key]
    entry = [param for param in params if ''.join(param['keys'])==''.join(key)]
    if entry:
        return entry[0]['name']
    else:
        return None
