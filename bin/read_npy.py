import numpy as np

# Inputs
fname = 'results.npy'
fname_xdata = 'results_xdata.npy'

results = np.load(fname)
xdata = np.load(fname_xdata)

# Save CSVs
np.savetxt('results_1100.csv', results[:,1,0,:], delimiter=',', fmt='%1.4e')
np.savetxt('results_1500.csv', results[:,5,0,:], delimiter=',', fmt='%1.4e')
np.savetxt('results_1800.csv', results[:,8,0,:], delimiter=',', fmt='%1.4e')
#np.savetxt('results_2000.csv', results[:,10,0,:], delimiter=',', fmt='%1.4e')
#np.savetxt('results_2500.csv', results[:,15,0,:], delimiter=',', fmt='%1.4e')
np.savetxt('results_xdata.csv', xdata, delimiter=',', fmt='%1.4e')
