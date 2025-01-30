import numpy as np

# Inputs
fname_sens = 'sens_co_n2o.npy'
fname_xdata = 'sens_xdata_co_n2o.npy'
nrxns = 9

sens = np.load(fname_sens)
xdata = np.load(fname_xdata)

# Save CSVs
np.savetxt('sens_1100.csv', np.transpose(sens[0,0:(nrxns+1),1,0,:]), delimiter=',')
np.savetxt('sens_1500.csv', np.transpose(sens[0,0:(nrxns+1),5,0,:]), delimiter=',')
np.savetxt('sens_1800.csv', np.transpose(sens[0,0:(nrxns+1),8,0,:]), delimiter=',')
np.savetxt('sens_xdata.csv', xdata, delimiter=',')
