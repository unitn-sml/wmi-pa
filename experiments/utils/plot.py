import json
import os
from collections import namedtuple, OrderedDict

import numpy as np
import pandas as pd

from wmipa import WMI
from wmipa.integration import LatteIntegrator, VolestiIntegrator, SymbolicIntegrator
from .io import check_path_exists
from .run import get_wmi_id

ERR_TOLERANCE = 1e-1  # absolute tolerance on value mismatch


def wmi_id_to_mode_id(wmi_id):
    if "volesti" in wmi_id:
        fields = wmi_id.split("_")
        # remove seed (second last field)
        fields = fields[:-2] + fields[-1:]
        return "_".join(fields)
    return wmi_id


def get_mode_id(mode, integrator):
    return wmi_id_to_mode_id(get_wmi_id(mode, integrator))


COLORS = ["#2f4f4f", "#7f0000", "#006400", "#4b0082", "#ff0000", "#00ff00", "#1e90ff", "#00ffff", "#f4a460", "#0000ff",
          "#d8bfd8", "#ff00ff", "#ffff54", "#00fa9a", "#ff69b4"]
ModeIdInfo = namedtuple("ModeIdInfo", ["color", "label"])
# Mode id sorted by order of appearance in the legend
MODE_IDS = OrderedDict([
    (get_mode_id("XADD", None), ModeIdInfo(COLORS[0], "XADD")),
    (get_mode_id("XSDD", None), ModeIdInfo(COLORS[1], "XSDD")),
    (get_mode_id("FXSDD", None), ModeIdInfo(COLORS[2], "FXSDD")),
    (get_mode_id(WMI.MODE_PA, LatteIntegrator()), ModeIdInfo(COLORS[3], "WMI-PA")),
    (get_mode_id(WMI.MODE_SA_PA, LatteIntegrator()), ModeIdInfo(COLORS[4], "SA-WMI-PA")),
    (get_mode_id(WMI.MODE_SA_PA_SK, LatteIntegrator()), ModeIdInfo(COLORS[5], "SA-WMI-PA-SK")),
    (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.1, N=100)),
     ModeIdInfo(COLORS[6], "SA-WMI-PA-SK(VolEsti, error=0.1, N=100)")),
    (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.1, N=1000)),
     ModeIdInfo(COLORS[7], "SA-WMI-PA-SK(VolEsti, error=0.1, N=1000)")),
    (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.1, N=10000)),
     ModeIdInfo(COLORS[8], "SA-WMI-PA-SK(VolEsti, error=0.1, N=10000)")),
    (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.1, N=100000)),
     ModeIdInfo(COLORS[11], "SA-WMI-PA-SK(VolEsti, error=0.1, N=100000)")),
    # (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.01, N=100000)),
    #  ModeIdInfo(COLORS[12], "SA-WMI-PA-SK(VolEsti, error=0.01, N=100000)")),
    # (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.01, N=1000000)),
    #  ModeIdInfo(COLORS[13], "SA-WMI-PA-SK(VolEsti, error=0.01, N=1000000)")),
    # (get_mode_id(WMI.MODE_SA_PA_SK, VolestiIntegrator(error=0.005, N=1000)),
    #  ModeIdInfo(COLORS[9], "SA-WMI-PA-SK(VolEsti, error=0.005)")),
    (get_mode_id(WMI.MODE_SA_PA_SK, SymbolicIntegrator()),
     ModeIdInfo(COLORS[10], "SA-WMI-PA-SK(Symbolic)")),
])


def get_input_files(input_paths):
    input_files = []
    input_paths = list(reversed(input_paths))
    while input_paths:
        input_path = input_paths.pop()
        check_path_exists(input_path)
        if os.path.isdir(input_path):
            input_paths.extend([os.path.join(input_path, f) for f in os.listdir(input_path)])
            continue
        assert os.path.isfile(input_path)
        _, ext = os.path.splitext(input_path)
        if ext == ".json":
            input_files.append(input_path)

    if not input_files:
        raise ValueError("No .json files found in the input folder")
    input_files = sorted(input_files)
    print("Files found:\n\t{}".format("\n\t".join(input_files)))
    return input_files


def parse_inputs(input_files, timeout):
    data = []
    for filename in input_files:
        with open(filename) as f:
            result_out = json.load(f)
        mode = result_out["mode"]
        if "integrator" not in result_out:
            print("Skipping file " + filename + " because it does not contain integrator key")
            continue
        integrator_info = result_out["integrator"]
        if integrator_info is not None:
            integrator_info = {f"integrator_{k}": v for k, v in result_out["integrator"].items()}
        else:
            integrator_info = {}

        assert "wmi_id" in result_out, f"File " + filename + " does not contain wmi_id key"
        wmi_id = result_out["wmi_id"]
        if "cache" in mode:
            continue
        for result in result_out["results"]:
            result["mode"] = mode
            result["wmi_id"] = wmi_id
            result.update(integrator_info)
        data.extend(result_out["results"])

    data = pd.DataFrame(data)

    data["mode_id"] = data["wmi_id"].apply(wmi_id_to_mode_id)
    data["filename"] = data["filename"].apply(os.path.basename)
    data["problem"] = data["filename"] + data["query"].apply(str)

    # deal with missing values and timeouts
    if timeout:
        data["parallel_time"] = data["parallel_time"].clip(upper=timeout)

    # set n_integrations = NaN where mode times out or where not available, so that they are not plotted
    data["n_integrations"] = data["n_integrations"].where(
        (data["parallel_time"] < timeout)
        & (data["parallel_time"].notna())
        & (data["n_integrations"] > 0),
        pd.NA,
    )

    return data.convert_dtypes()


def check_values(data: pd.DataFrame, ref="SAPASK_latte"):
    """Check if the values of the different modes match with the reference mode "ref" (where not NaN)

    """

    data = (
        data.groupby(["problem", "wmi_id"])
        .aggregate(time=("parallel_time", "first"),
                   value=("value", "first"),
                   count=("parallel_time", "count"))
        .astype({"value": np.float64})
        .unstack()
    )

    # ensure we have no duplicated output
    assert (data["count"] == 1).all().all(), "Some output are duplicated: {}".format(
        data[data["count"] != 1]["count"]
    )

    # check values match with the reference mode "ref" (where not NaN)
    ii = data["value", ref].notna()
    modes = data.columns.get_level_values(1).unique()
    print(modes)
    for mode in modes:
        indexes = ii & data["value", mode].notna()
        # check if results agree with "ref" with a relative tolerance of ERR_TOLERANCE.
        # TODO: maybe we should check using the integrator_error instead of ERR_TOLERANCE, but currently we cannot
        #  trust the guarantees given by VolEsti.

        diff = ~np.isclose(
            data[indexes]["value", mode].values,
            data[indexes]["value", ref].values,
            rtol=ERR_TOLERANCE,
        )
        if diff.any():
            print("Error! {}/{} values of {} do not match with {}".format(diff.sum(), indexes.sum(), mode, ref))
            # print(data[indexes][diff]["value"][[ref, mode]])
        else:
            print("Mode {:10s}: {:4d} values OK".format(mode, indexes.sum()))
