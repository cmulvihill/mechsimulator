import numpy as np

CSV_PATH = 'csv_files'

# Inputs
names = [
    'Alturaifi_NH3-Ar',
    'Alturaifi_NH3-H2-Ar',
    'Michel1965_N2H4-Ar,0_32%',
    'Michel1965_N2H4-Ar,0_11%',
    'Benes2021_NH3-Ar', 
    'Benes2021_NH3-N2', 
]

for name in names:
    xdata = np.load(f'results_xdata_{name}.npy')
    ydata = np.load(f'results_{name}.npy')
    if 'Alturaifi' in name:
        xy_data_mech1 = np.transpose(np.concatenate((xdata[np.newaxis, :], ydata[0,:,0,:])))
        xy_data_mech2 = np.transpose(np.concatenate((xdata[np.newaxis, :], ydata[1,:,0,:])))
    elif 'Michel' in name:
        xy_data_mech1 = np.vstack((xdata[:], ydata[0,:,0]))
        xy_data_mech2 = np.vstack((xdata[:], ydata[1,:,0]))
    elif 'Benes' in name:
        #xy_data_mech1 = np.transpose(np.hstack((xdata[:, np.newaxis], ydata[0,:,:])))
        #xy_data_mech2 = np.transpose(np.hstack((xdata[:, np.newaxis], ydata[1,:,:])))
        xy_data_mech1 = np.hstack((xdata[:, np.newaxis], ydata[0,:,:]))
        xy_data_mech2 = np.hstack((xdata[:, np.newaxis], ydata[1,:,:]))
        
    np.savetxt(f'{CSV_PATH}/results_{name}_mech1.csv', xy_data_mech1, delimiter=',', fmt='%1.4e')
    np.savetxt(f'{CSV_PATH}/results_{name}_mech2.csv', xy_data_mech2, delimiter=',', fmt='%1.4e')

