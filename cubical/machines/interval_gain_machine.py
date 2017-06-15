from abc import ABCMeta, abstractmethod
import numpy as np
from cubical.flagging import FL
from cubical.machines.abstract_machine import MasterMachine
from functools import partial

class PerIntervalGains(MasterMachine):
    """
    This is a base class for all gain solution machines that use solutions intervals.
    """

    def __init__(self, model_arr, times, frequencies, options):
        """
        Given a model array, initializes various sizes relevant to the gain solutions.
        """

        MasterMachine.__init__(self, times, frequencies)

        self.n_dir, self.n_mod, self.n_tim, self.n_fre, self.n_ant, self.n_ant, self.n_cor, self.n_cor = model_arr.shape
    
        self.dtype = model_arr.dtype
        self.ftype = model_arr.real.dtype
        self.t_int = options["time-int"]
        self.f_int = options["freq-int"]
        self.eps = 1e-6

        # n_tim and n_fre are the time and frequency dimensions of the data arrays.
        # n_timint and n_freint are the time and frequnecy dimensions of the gains.

        self.n_timint = int(np.ceil(float(self.n_tim) / self.t_int))
        self.n_freint = int(np.ceil(float(self.n_fre) / self.f_int))
        self.n_tf_ints = self.n_timint * self.n_freint

        # Total number of solutions.

        self.n_sols = float(self.n_dir * self.n_tf_ints)

        # Initialise attributes used for computing values over intervals.

        self.t_bins = range(0, self.n_tim, self.t_int)
        self.f_bins = range(0, self.n_fre, self.f_int)

        # Initialise attributes used in convergence testing. n_cnvgd is the number
        # of solutions which have converged.

        self.n_cnvgd = 0 

        # Construct the appropriate shape for the gains.

        self.gain_shape = [self.n_dir, self.n_timint, self.n_freint, self.n_ant, self.n_cor, self.n_cor]

        # Construct flag array

        self.flag_shape = [self.n_dir, self.n_timint, self.n_freint, self.n_ant]
        self.gflags = np.zeros(self.flag_shape, FL.dtype)
        self.flagbit = FL.ILLCOND

    def compute_stats(self, flags, eqs_per_tf_slot):
        """
        This method computes various stats and totals based on the current state of the flags.
        These values are used for weighting the chi-squared and doing intelligent convergence
        testing.
        """

        # (n_timint, n_freint) array containing number of valid equations per each time/freq interval.

        self.eqs_per_interval = self.interval_sum(eqs_per_tf_slot)

        # The following determines the number of valid (unflagged) time/frequency slots and the number
        # of valid solution intervals.

        self.valid_intervals = self.eqs_per_interval>0
        self.num_valid_intervals = self.valid_intervals.sum()

        # Pre-flag gain solution intervals that are completely flagged in the input data 
        # (i.e. MISSING|PRIOR). This has shape (n_timint, n_freint, n_ant).

        missing_gains = self.interval_and((flags&(FL.MISSING|FL.PRIOR) != 0).all(axis=-1))

        # Gain flags have shape (n_dir, n_timint, n_freint, n_ant). All intervals with no prior data
        # are flagged as FL.MISSING.
        
        self.gflags[:, missing_gains] = FL.MISSING
        self.missing_gain_fraction = missing_gains.sum() / float(missing_gains.size)

    def interval_sum(self, arr, tdim_ind=0):
   
        return np.add.reduceat(np.add.reduceat(arr, self.t_bins, tdim_ind), self.f_bins, tdim_ind+1)

    def interval_and(self, arr, tdim_ind=0):
   
        return np.logical_and.reduceat(np.logical_and.reduceat(arr, self.t_bins, tdim_ind), self.f_bins, tdim_ind+1)





