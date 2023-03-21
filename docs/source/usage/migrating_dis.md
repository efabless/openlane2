# Migrating `DIODE_INSERTION_STRATEGY`

As they were extremely complex, the OpenLane 1.0 diode insertion strategies were replaced by two flags in OpenLane 2's "Classic" flow:

* `GRT_REPAIR_ANTENNAS`: Attempts to repair antenna during the GRT step using OpenROAD's `repair_antennas` function.
* `RUN_HEURISTIC_DIODE_INSERTION`: Runs a custom script by [Sylvain Munaut](https://github.com/smunaut) that inserts diodes based on a net's Manhattan distance at global placement time.

The mapping for the strategies is as follows:

* Strategies 1, 2 and 5 will throw an error.
    * 1 is an unreasonable brute force approach that adds a diode to every single net. 2 and 5 utilize replacable "fake diode" fill cells, which are a hack that will not be available in all PDKs.

* Strategy 0:
    * Both flags are set to `false`.
* Strategy 3:
    * `GRT_REPAIR_ANTENNAS` is set to `true`.
* Strategy 5:
    * `RUN_HEURISTIC_DIODE_INSERTION` is set to `true`.
* Strategy 6:
    * Both flags are set to `true`.

Although for now OpenLane 2 will attempt the conversion for you automatically, it is recommended you update your designs as this feature will get removed.