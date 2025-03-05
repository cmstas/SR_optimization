```conversion_helper.sh```

    * A simple shell script that handles all the options, mass points, signal region binning, etc

```convert_HiggsDNA_to_FggFF.py```

    * Actually handles the mechanics of the conversion

There is a known warning
```
UserWarning: converter for dtype('O') is not implemented (skipping)
    cobj = _librootnumpy.array2tree_toCObj(arr, name=name, tree=incobj)
```
This is not a problem. This workflow relies on the depricated ```root_numpy``` and ```root_pandas``` packages.
A full conversion to ```uproot``` should be applied at some point
