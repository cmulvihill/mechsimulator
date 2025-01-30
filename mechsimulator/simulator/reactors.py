import numpy as np
from scipy.interpolate import RegularGridInterpolator
import cantera as ct


def st(temp, pressure, mix, gas, targ_spcs, end_time, p_of_t=None):
    """ Runs a shock tube simulation; the non-ideal pressure rise, dP/dt,
        can be incorporated via an optional P(t) profile

        :param temp: reactor inlet temperature (Kelvin)
        :type temp: float
        :param pressure: reactor constant pressure (atm)
        :type pressure: float
        :param mix: initial species concentrations at reactor inlet
        :type mix: dct {spc1: conc1, spc2: ...}
        :param gas: a Cantera object describing a kinetics mechanism/gas
        :type gas: Cantera Solution object
        :param targ_spcs: desired species concentrations
        :type targ_spcs: list [spc1, spc2, ...]
        :param end_time: end time for the simulation (s); simulation will end
            at the first of either this time or the max time in p_of_t
        :type end_time: float
        :param p_of_t: specified pressure (any units) vs time (s) profile;
            can be None if no non-ideal effects are being simulated
        :type p_of_t: Numpy array of shape (2, num_exp_timesteps)
        :return targ_concs: targ_spcs mole fractions at each time
        :rtype: Numpy array of shape (num_targ_spcs, num_timesteps)
        :return times: array of time values (s)
        :rtype: Numpy array of shape (num_timesteps,)

        Note: the timesteps of the p_of_t and the simulation results do not have
            to be (and likely will not be) the same length
    """

    def _wall_velocity(time):
        """ Gets the wall velocity at some time based on v_of_t

            :param time: individual time value (s)
            :type time: float
            :return vel: velocity of the wall (m/s)
            :rtype: float
        """
        dvdt = np.gradient(v_of_t[1, :], v_of_t[0, :])
        dxdt = dvdt / wall.area  # only for clarity (since A = 1 m^2)
        vel = np.interp(time, v_of_t[0, :], -1 * dxdt)

        return vel

    gas = _set_state(gas, temp, pressure, mix)

    if p_of_t is None:
        # Create an array of ones spanning from t=0 to t=end_time
        v_of_t = np.array([[0, end_time], [1, 1]])
    else:
        # Convert P(t) to V(t) assuming isentropic behavior
        gamma = gas.cp_mass / gas.cv_mass  # specific heat ratio
        v_of_t = np.zeros_like(p_of_t)
        v_of_t[0, :] = p_of_t[0, :]  # time values are the same
        v_of_t[1, :] = (p_of_t[1, :] / p_of_t[1, 0]) ** (-1 / gamma)

    # Set up reactor, wall, and network
    reac = ct.IdealGasReactor(gas)
    reac.volume = 1  # m^3 (default value, but here for clarity)
    env = ct.Reservoir(gas)
    wall = ct.Wall(env, reac)
    wall.area = 1  # m^2 (default value, but here for clarity)
    wall.heat_transfer_coeff = 0  # no heat transfer considerations for ST
    wall.set_velocity(_wall_velocity)
    network = ct.ReactorNet([reac])
    #network.atol = 1e-20
    #network.rtol = 1e-15
    # network.set_max_time_step(np.max(np.diff(v_of_t[0, :])))

    # Run the simulation
    time = 0
    states = ct.SolutionArray(gas, extra=['t'])
    states.append(reac.thermo.state, t=time)
    while time < np.min([end_time, v_of_t[0, -1]]):
        time = network.step()
        states.append(reac.thermo.state, t=time)

    # Get results
    times = states.t
    pressures = states.P
    temps = states.T
    targ_concs = np.zeros((len(targ_spcs), len(times)))
    for idx, targ_spc in enumerate(targ_spcs):
        if targ_spc is not None:
            targ_concs[idx, :] = states.X[:, gas.species_index(targ_spc)]
        else:
            targ_concs[idx, :] = np.nan

    rop = None  # will develop later...
    end_gas = gas

    return targ_concs, pressures, temps, times, rop, end_gas


def rcm(temp, pressure, mix, gas, targ_spcs, end_time, v_of_t):
    """ Runs a rapid compression machine simulation, with compression and heat
        loss incorporated via an input V(t) profile

        :param temp: reactor inlet temperature (Kelvin)
        :type temp: float
        :param pressure: reactor constant pressure (atm)
        :type pressure: float
        :param mix: initial species concentrations at reactor inlet
        :type mix: dct {spc1: conc1, spc2: ...} (example:
            {'H2': 0.5, 'O2': 0.5})
        :param gas: a Cantera object describing a kinetics mechanism/gas
        :type gas: Cantera Solution object
        :param targ_spcs: desired species concentrations
        :type targ_spcs: list [spc1, spc2, ...]
        :param end_time: end time for the simulation (s); simulation will end
            at the first of either this time or the max time in v_of_t
        :type end_time: float
        :param v_of_t: specified volume (any units) vs time (s) profile
            to account for both piston compression and heat loss
        :type v_of_t: Numpy array of shape (2, num_times), where
            index 0 is time and index 1 is volume
        :return pressures: calculated pressure (Pa)
        :rtype: Numpy array of shape (num_times)
        :return times: time array corresponding to pressures (s)
        :rtype: Numpy array of shape (num_times)
    """

    def _piston_velocity(time):
        """ Gets the piston velocity at some time based on v_of_t

            :param time: individual time value (s)
            :type time: float
            :return vel: velocity of the piston (m/s)
            :rtype: float
        """
        dvdt = np.gradient(v_of_t[1, :], v_of_t[0, :])
        dxdt = dvdt / piston.area  # only for clarity (since area = 1 m^2)
        vel = np.interp(time, v_of_t[0, :], -1 * dxdt)

        return vel

    gas = _set_state(gas, temp, pressure, mix)

    print('inside reactors, rcm temp: ', temp)
    # Normalize the volume profile by the first value
    v_of_t[1, :] = v_of_t[1, :] / v_of_t[1, 0]

    # Set up reactor, piston, and network
    reac = ct.IdealGasReactor(gas)
    reac.volume = 1  # m^3
    env = ct.Reservoir(gas)
    piston = ct.Wall(env, reac)
    piston.area = 1  # m^2 (this is the default, but put here for clarity)
    piston.heat_transfer_coeff = 0  # instead, considering heat trans. w/volume
    piston.set_velocity(_piston_velocity)
    network = ct.ReactorNet([reac])
    # network.set_max_time_step(np.max(np.diff(v_of_t[0, :])))

    # Run the simulation
    time = 0
    states = ct.SolutionArray(gas, extra=['t'])
    states.append(reac.thermo.state, t=time)
    while time < np.min([end_time, v_of_t[0, -1]]):
        time = network.step()
        states.append(reac.thermo.state, t=time)

    # Get results
    times = states.t
    pressures = states.P
    targ_concs = np.zeros((len(targ_spcs), len(times)))
    for idx, targ_spc in enumerate(targ_spcs):
        targ_concs[idx, :] = states.X[:, gas.species_index(targ_spc)]
    end_gas = gas
    rop = None  # temporary

    return targ_concs, pressures, times, rop, end_gas


def pfr(temp, pressure, mix, gas, targ_spcs, mdot, area, length,
        res_time=None, n_steps=2000, x_profile=None, t_profile=None,
        t_profile_setpoints=None):
    """ Runs a plug flow reactor simulation

        :param temp: reactor inlet temperature (Kelvin)
        :type temp: float
        :param pressure: reactor constant pressure (atm)
        :type pressure: float
        :param mix: initial species concentrations at reactor inlet
        :type mix: dct {spc1: conc1, spc2: ...}
            (example: {'H2': 0.5, 'O2': 0.5})
        :param gas: a Cantera object describing a kinetics mechanism/gas
        :type gas: Cantera Solution object
        :param targ_spcs: desired species concentrations
        :type targ_spcs: list [spc1, spc2, ...]
        :param mdot: reactor mass flow rate (kg/s)
        :type mdot: float
        :param area: reactor cross-sectional area (m^2)
        :type area: float
        :param length: reactor length (m)
        :type length: float
        :param res_time: reactor residence time (s); should only be given if
            mdot is None
        :type res_time: float
        :param n_steps: approx. number of steps to take; used to guess timestep
            (note: will almost NEVER be the actual number of timesteps taken)
        :type n_steps: int
        :return targ_concs: targ_spcs mole fractions at each time/position
        :rtype: Numpy array of shape (num_targs, num_times)
        :return times: time values at each solver step
        :rtype: Numpy array of shape (num_times,)
        :return positions: position values at each solver step
        :rtype: Numpy array of shape (num_times,)
    """

    # Set the initial gas state
    if x_profile is not None:  # use T profile if given
        # Create the 2D array
        t_data = np.ndarray((len(x_profile[0]), len(t_profile_setpoints)))
        for idx, array in enumerate(t_profile):
            t_data[:, idx] = array
        # Create the interp object and interp (note: the [0] gets rid of uncertainties)
        interp = RegularGridInterpolator((x_profile[0], t_profile_setpoints), t_data)
        start_temp = interp((0, temp))
        gas = _set_state(gas, start_temp, pressure, mix)
    else:  # otherwise, just use the given, fixed T
        gas = _set_state(gas, temp, pressure, mix)

    # Create reactor and reactor network
    reac = ct.IdealGasConstPressureReactor(gas)
    network = ct.ReactorNet([reac])

    # Approximate a time step
    density, _ = gas.DP  # kg/m^3
    if res_time is not None:  # if res_time was given instead of mdot
        mdot = (density * area * length) / res_time  # kg/s
    inlet_velocity = mdot / (density * area)  # m/s
    dt = (length / inlet_velocity) / n_steps  # s

    # Initialize time, position, velocity, and thermo states
    times = (np.arange(n_steps * 2) + 1) * dt  # longer than needed to be safe
    positions = np.zeros_like(times)
    velocities = np.zeros_like(times)
    states = ct.SolutionArray(reac.thermo)

    # Loop over each timestep
    end_idx = len(times) - 1  # defining as backup; should be overwritten
    for idx, time in enumerate(times):
        network.advance(time)  # perform time integration
        velocities[idx] = mdot / area / reac.thermo.density
        positions[idx] = positions[idx - 1] + velocities[idx] * dt  # transform
        states.append(reac.thermo.state)

        # If the reactor length has been exceeded, exit the for loop
        if positions[idx] >= length:
            end_idx = idx
            break

        # If a T profile was given, update the temperature
        if t_profile is not None:
            new_temp = interp((positions[idx], temp))  # use *given* T to get profile
            thermo = reac.thermo
            thermo.TPX = new_temp, thermo.TPX[1], thermo.TPX[2]
            reac.insert(thermo)
            network.reinitialize()

    # Removed unused entries in time and position
    times = times[:(end_idx + 1)]
    positions = positions[:(end_idx + 1)]

    # Get results for target species
    targ_concs = np.full((len(targ_spcs), end_idx + 1), np.nan)
    for idx, targ_spc in enumerate(targ_spcs):
        if targ_spc is not None:
            targ_concs[idx, :] = states.X[:, gas.species_index(targ_spc)]

    end_gas = gas
    rop = None

    return targ_concs, times, positions, rop, end_gas


def jsr(temp, pressure, mix, gas, targ_spcs, res_time, vol, prev_concs=None,
        mdot=None, max_iter=30000):
    """ Runs a jet-stirred reactor simulation

        :param temp: reactor inlet temperature (Kelvin)
        :type temp: float
        :param pressure: reactor constant pressure (atm)
        :type pressure: float
        :param mix: initial species concentrations at reactor inlet
        :type mix: dct {spc1: conc1, spc2: ...} (example:
            {'H2': 0.5, 'O2': 0.5})
        :param gas: a Cantera object describing a kinetics mechanism/gas
        :type gas: Cantera Solution object
        :param targ_spcs: desired species concentrations
        :type targ_spcs: list [spc1, spc2, ...]
        :param res_time: reactor residence time (s)
        :type res_time: float
        :param vol: volume of the reactor (m^3)
        :type vol: float
        :param prev_concs: species concentrations from previous solution at
            a similar condition
        :type prev_concs: numpy array of shape (nspcs_in_mechanism,)
        :param mdot: mass flow rate (kg/s); should only be given if res_time is
            None
        :type mdot: float
        :param max_iter: max number of timesteps to achieve steady state
        :type max_iter: int
        :return targ_concs: outlet concentrations of targ_spcs
        :rtype: Numpy array of shape (ntargs,)
        :return all_concs: outlet concentrations of all species in mech
        :rtype: Numpy array of shape (nspcs_in_mechanism,)
    """

    # Note: must set gas with mix before creating reservoirs!
    gas = _set_state(gas, temp, pressure, mix)
    inlet = ct.Reservoir(gas)
    exhaust = ct.Reservoir(gas)

    # Create reactor, using prev_concs to speed up convergence
    prev_concs_input = True
    if prev_concs is None:
        prev_concs_input = False
        prev_concs = mix
    gas = _set_state(gas, temp, pressure, prev_concs)
    reac = ct.IdealGasReactor(gas, energy='off', volume=vol)

    # Set up devices
    pressure_valve_coeff = 0.01  # "conductance" of the pressure valve
    ct.Valve(upstream=reac, downstream=exhaust, K=pressure_valve_coeff)
    if res_time is not None:  # MFC condition depends on inputs
        ct.MassFlowController(upstream=inlet, downstream=reac,
                              mdot=reac.mass / res_time)
    elif mdot is not None:
        ct.MassFlowController(upstream=inlet, downstream=reac, mdot=mdot)

    # Create reactor network (only the JSR in this case) and advance it to SS
    reac_net = ct.ReactorNet([reac])
    failure = False
    try:
        reac_net.advance_to_steady_state(max_steps=max_iter)
        all_concs = reac.thermo.X  # store output concentrations
    except ct._cantera.CanteraError as ct_error:
        failure = True
        print(f"JSR solver failed at {temp} K for mechanism {gas.name}. The "
              f"error was:\n{ct_error}")
        # If no initial guess, set results to None for next iteration
        if prev_concs_input is False:
            all_concs = None
        # If an initial guess was input, return it for use in the next iteration
        else:
            all_concs = prev_concs

    # Get results for target species
    targ_concs = np.zeros(len(targ_spcs))
    for idx, targ_spc in enumerate(targ_spcs):
        if failure:
            targ_concs[idx] = None
        else:
            if targ_spc in gas.species_names:
                targ_concs[idx] = all_concs[gas.species_index(targ_spc)]
            else:  # if the targ_spc isn't in the mechanism
                targ_concs[idx] = None
    end_gas = gas
    rop = None

    return targ_concs, all_concs, rop, end_gas


def const_t_p(temp, pressure, mix, gas, targ_spcs, end_time):
    """ Runs a constant-temperature, constant-pressure 0-D simulation

        :param temp: reactor inlet temperature (Kelvin)
        :type temp: float
        :param pressure: reactor constant pressure (atm)
        :type pressure: float
        :param mix: initial species concentrations at reactor inlet
        :type mix: dct {spc1: conc1, spc2: ...} (example:
            {'H2': 0.5, 'O2': 0.5})
        :param gas: a Cantera object describing a kinetics mechanism/gas
        :type gas: Cantera Solution object
        :param targ_spcs: desired species concentrations
        :type targ_spcs: list [spc1, spc2, ...]
        :param end_time: end time for the simulation (s)
        :type end_time: float
        :return targ_concs: targ_spcs mole fractions at each time
        :rtype: Numpy array of shape (ntargs, ntimes)
        :return times: array of time values (s)
        :rtype: Numpy array of shape (ntimes,)
    """

    gas = _set_state(gas, temp, pressure, mix)

    # Setting energy to 'off' holds T constant
    reac = ct.IdealGasConstPressureReactor(gas, energy='off')
    network = ct.ReactorNet([reac])

    # Run the simulation
    time = 0
    states = ct.SolutionArray(gas, extra=['t'])
    states.append(reac.thermo.state, t=time)
    while time < end_time:
        time = network.step()
        states.append(reac.thermo.state, t=time)

    # Get results
    times = states.t
    pressures = states.P
    temps = states.T
    targ_concs = np.zeros((len(targ_spcs), len(times)))
    for idx, targ_spc in enumerate(targ_spcs):
        if targ_spc is not None:
            targ_concs[idx, :] = states.X[:, gas.species_index(targ_spc)]
        else:
            targ_concs[idx, :] = np.nan

    rop = None  # will develop later...
    end_gas = gas

    return targ_concs, pressures, temps, times, rop, end_gas


def free_flame(temp, pressure, mix, gas, targ_spcs, prev_soln=None):
    """ Runs an adiabatic, 1-D, freely propagating flame simulation

        NOTE: need to add options for simulation details

        :param temp: reactor inlet temperature (Kelvin)
        :type temp: float
        :param pressure: reactor constant pressure (atm)
        :type pressure: float
        :param mix: initial species concentrations at reactor inlet
        :type mix: dct {spc1: conc1, spc2: ...} (example:
            {'H2': 0.5, 'O2': 0.5})
        :param gas: a Cantera object describing a kinetics mechanism/gas
        :type gas: Cantera Solution object
        :param targ_spcs: desired species concentrations
        :type targ_spcs: list [spc1, spc2, ...]
        :param prev_soln: previous temperature profile vs. position; first
            column is position, second is temperature
        :type prev_soln: Numpy array of shape (2, npoints)
        :return targ_concs: targ_spcs mole fractions at each grid point
        :rtype: Numpy array of shape (ntargs, npoints)
        :return pos: array of grid positions (m)
        :rtype: Numpy array of shape (npoints,)
        :return vels: gas velocities at each position (m/s)
        :rtype: Numpy array of shape (npoints,)
        :return temps: gas temperatures at each position (K)
        :rtype: Numpy array of shape (npoints,)
        :return rop: rate-of-production for each target species at each position
            (not sure of units...check Cantera once I get RoP working)
        :rtype: not sure
        :return end_gas: Cantera solution object. Needs to be at a specific
            flame location...will need to figure this one out
        :rtype: Cantera Solution object
    """

    # Initialize things
    gas = _set_state(gas, temp, pressure, mix)
    loglevel = 0  # for now, suppress all output
    flame = ct.FreeFlame(gas)
    flame.transport_model = 'Mix'
    if prev_soln is not None:
        flame.set_profile('T', prev_soln[0, :], prev_soln[1, :])

    # Run the simulation
    try:
        flame.solve(loglevel=loglevel, auto=True)
    except ct._cantera.CanteraError as ct_error:
        print(f"Free flame solver failed at {temp} K, {pressure} atm, mix: "
              f"{mix}. The error was:\n{ct_error}")

    # Get the target concentrations
    npoints = np.shape(flame.X)[1]  # length of second dim is npoints
    targ_concs = np.ndarray((len(targ_spcs), npoints))
    for targ_idx, targ_spc in enumerate(targ_spcs):
        if targ_spc in gas.species_names:
            targ_concs[targ_idx] = flame.solution(targ_spc)
        else:  # if the targ_spc isn't in the mechanism
            targ_concs[targ_idx] = np.nan

    # Get other results
    pos = flame.grid
    vels = flame.velocity
    temps = flame.T
    rop = None  # not sure what to do here
    end_gas = None  # will develop later

    return targ_concs, pos, vels, temps, rop, end_gas


def burner():
    # Coming soon...
    pass


def _set_state(gas, temp, pressure, mix):
    """ Sets a gaseous mixture to a desired thermodynamic state

        :param gas: Cantera Solution object describing some mixture
        :type gas: Cantera Solution object
        :param temp: temperature (K)
        :type temp: float
        :param pressure: pressure (atm)
        :type pressure: float
        :param mix: mixture description; either in terms of equivalence ratio
            (phi) (e.g., {'phi': 0.5, 'fuel': ['H2',], 'oxid': ['O2', 'N2'],
            'oxid_ratios': [1, 3.76]}) or in terms of mole fractions (e.g.,
            {'H2': 0.25, 'O2': 0.3, 'N2': 0.45}
        :type mix: dict
        :return gas: Cantera Solution object that has been set to the desired
            thermodynamic state
        :rtype: Cantera Solution object
    """
    def _mix_str(mix, type):
        """ Converts mix to a string
        :param type: either 'fuel' or 'oxid'
        """
        mix_str = ''
        ncomps = len(mix[type])  # number of components
        for idx in range(ncomps):
            spc = mix[type][idx]
            if ncomps > 1:
                ratio = 4

    pressure = pressure * 101325  # atm to Pa

    if isinstance(mix, dict) and 'fuel' in mix:  # if mix defined using phi
        # Create string for fuel species
        fuel = ''
        nfuels = len(mix['fuel'])
        for idx in range(nfuels):
            spc = mix['fuel'][idx]
            if nfuels > 1:
                ratio = mix['fuel_ratios'][0][idx]
                fuel += f'{spc}: {ratio}'
                if idx + 1 < nfuels:  # if not on last spc, add a comma
                    fuel += ', '
            else:
                fuel += spc
        # Create string for oxidizer species
        oxid = ''
        noxids = len(mix['oxid'])
        for idx in range(noxids):
            spc = mix['oxid'][idx]
            if noxids > 1:
                ratio = mix['oxid_ratios'][0][idx]
                oxid += f'{spc}: {ratio}'
                if idx + 1 < noxids:  # if not on last spc, add a comma
                    oxid += ', '
            else:
                oxid += spc

        phi = mix['phi']
        gas.set_equivalence_ratio(phi, fuel, oxid, basis='mole')
        gas.TP = temp, pressure

    else:  # if mix is defined in terms of mole fractions
        gas.TPX = temp, pressure, mix

    return gas
