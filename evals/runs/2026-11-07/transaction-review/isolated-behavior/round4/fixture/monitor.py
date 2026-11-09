"""合成任务监控。只在本 fixture 中使用，不连接外部系统。"""
import argparse
import json
from pathlib import Path


def run(config, event):
    state = {"owner": "TaskRunner", "status": "RUNNING", "error_count": 0}
    log = []
    subscriptions = {config["error_topic"]: lambda: state.update(status="FAILED", error_count=state["error_count"] + 1)}
    if event == "success":
        state["status"] = "SUCCEEDED"
        log.append({"source": "TaskRunner", "event": "success"})
    elif event == "error":
        emitted_topic = "task.error"
        log.append({"source": "TaskRunner", "event": emitted_topic, "request_id": "fixture-001"})
        callback = subscriptions.get(emitted_topic)
        if callback is not None:
            callback()
            log.append({"source": "ErrorProbe", "event": "observed_error"})
    return {"ui": {"button_enabled": False}, "monitor": state, "source_log": log}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=str(Path(__file__).with_name("config.json")))
    p.add_argument("--event", choices=["idle", "success", "error"], required=True)
    args = p.parse_args()
    print(json.dumps(run(json.loads(Path(args.config).read_text()), args.event), indent=2))
