"""IDA -S entry point. Reads JSON only, never executes config-provided Python.
Usage (verify executable/options in installed IDA):
  idat -A -Lrun.log -S"/path/run_ida_batch.py /path/job.json" /path/work-copy.i64
No automatic save or qexit: caller owns lifecycle, preserving failure inspection.
For idalib, open an authorized working database then call run(config) on its owner thread.
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ida_evidence import export, report, wait_for_analysis


def run(config):
    if config.get("wait_for_analysis", False):
        # This permission is separate from read-only extraction.
        wait_for_analysis()
    result = report(config["operation"], *config.get("args", []), **config.get("kwargs", {}))
    # 导出状态是调用返回值的附加证据，不改写已发布的分析文件。
    result["export_status"] = export(result, config["output"], config.get("format", "json"), return_status=True)
    try:
        print("SkillForge result: ok=%s seconds=%.3f output=%s published=%s cleanup_error=%s" %
              (result["ok"], result["seconds"], config["output"],
               result["export_status"]["published"], result["export_status"]["cleanup_error"]))
    except (OSError, ValueError) as exc:
        # 关闭的stdout不能把已发布结果变成未知失败；由返回值保留诊断。
        result["export_status"]["diagnostic_error"] = str(exc)
    return result


if __name__ == "__main__":
    import idc
    if len(idc.ARGV) != 2:
        raise RuntimeError("Expected exactly one JSON job path after script name")
    with open(idc.ARGV[1], "r", encoding="utf-8") as stream:
        run(json.load(stream))
