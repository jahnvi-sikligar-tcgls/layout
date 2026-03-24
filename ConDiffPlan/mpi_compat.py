"""
Minimal mpi4py compatibility layer for single-process execution.
"""


class _SingleProcessComm:
    rank = 0
    size = 1

    def Get_rank(self):
        return 0

    def Get_size(self):
        return 1

    def bcast(self, value, root=0):
        return value


class _MPICompat:
    COMM_WORLD = _SingleProcessComm()


MPI = _MPICompat()
