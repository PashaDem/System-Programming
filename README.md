## The project that executes the MapReduce algorithm in parallel using multi-processing and the following syncronization or additional elements:

- Queue - a thread-safe collection of elements based on FIFO principle. Is used for storing string-values that contain information on what processes has processed the data chunk and related timestamp of this action.
- Lock - the lock object for synchronization of the access to the `partition_counter` int object for statistics on how many data chunks were processed.
- Process Pool - creates the pool of processes and maps particular processes with related tasks
