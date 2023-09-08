import sys
from mechsimulator import runner

JOB_FILES = [
    # 'dme_sandia.xlsx',
    #'dme_sandia_sens.xlsx',
    # 'dme_sandia_jsr_only.xlsx',
    # 'butane_jsr.xlsx'
    # 'madeup_h2o2_jsr.xlsx',
    # 'madeup_h2o2_st_idt.xlsx',
    # 'pham_n2o+o_check.xlsx'
    # 'n2o+o(1d)_tests.xlsx'
    # 'davidson_1990_sens.xlsx'
    # 'ro2_oh_idt_sens_c2h6.xlsx'
    # 'dme_sandia_515.xlsx',
    # 'c3h8_curran_tests.xlsx'
    # 'dme_sandia_513.xlsx',
    #'dme_sandia_qooh_and_roo.xlsx',
    # 'c3h8_rcm_dames_2016.xlsx'
    # 'h2o2_test_rcm.xlsx'
    #'iso-octane_minetti.xlsx'
    #'iso-octane_fang2020.xlsx'
    #'mulvihill_n2o_ar.xlsx'
    #'mulvihill_n2o_ar_sens.xlsx'
    #'mulvihill_n2o_n2.xlsx'
    #'ro2_oh_idt_sens_c2h6_updated.xlsx'
    #'dme_sandia_T_scan_only.xlsx' 
    #'dme_sandia_qooh_and_roo.xlsx' 
    #'dme_sandia_ro_raghu.xlsx'
    'lfs_test.xlsx'
    #'dme_sandia_test.xlsx',
    #'dme_sandia_ro2_qooh.xlsx',
    #'dme_sandia_qooh_2ch2o_oh.xlsx',
    #'dme_sandia_qooh_o2_ooqooh.xlsx',
    #'dme_sandia_both_qooh_roo.xlsx',
    #'dme_sandia_no_bimol.xlsx',
    #'dme_sandia_for_raghu.xlsx',
    #'dme_sandia_pathways.xlsx',
    # 'stagni_2020_pfr.xlsx',
    #'run_nh3_synth.xlsx',
    #'run_nh3_decomp_impure_5perc.xlsx',
    #'run_ronney_1988_nh3_lfs.xlsx',
]

runner.main.run_jobs(JOB_FILES)
