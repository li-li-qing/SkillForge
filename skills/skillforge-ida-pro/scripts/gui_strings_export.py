"""IDA GUI字符串分片导出；失败保留.partial，只有完整关闭后发布最终文件。
目标IDA9.x，尚未真实GUI验证。保持数据库和Strings列表不变。
"""
import json
import os
import time
from ida_evidence import context, hex_ea, module, ready
_JOB = None
_LAST_RESULT = None


def status():
    """状态是本进程内证据；不是文件持久化或崩溃恢复保证。"""
    if _JOB is not None:
        return {"state":"running", "count":_JOB["count"], "path":_JOB["path"]}
    return dict(_LAST_RESULT) if _LAST_RESULT is not None else {"state":"idle"}


def _finish(job, event, error=None):
    global _JOB, _LAST_RESULT
    errors = [] if error is None else [str(error)]
    published = False
    try:
        try:
            job["stream"].write(json.dumps({"event":event, "count":job["count"],
                "seconds":time.monotonic()-job["started"],"error":error})+"\n")
            job["stream"].flush()
            os.fsync(job["stream"].fileno())
        except Exception as exc:
            errors.append("terminal write/flush/fsync: "+str(exc))
        finally:
            try:
                job["stream"].close()
            except Exception as exc:
                errors.append("close: "+str(exc))
        if event == "complete" and not errors:
            try:
                # 同目录硬链接提供无覆盖发布；目标已存在或不支持时保留partial。
                os.link(job["partial_path"],job["path"])
                published = True
            except Exception as exc:
                errors.append("publish: "+str(exc))
        cleanup_error = None
        if published:
            try:
                os.unlink(job["partial_path"])
            except Exception as exc:
                cleanup_error = str(exc)  # 最终文件已完整发布，仅残留重复partial。
        _LAST_RESULT = {"state":"complete" if published else "cancelled" if event=="cancelled" and not errors else "failed",
            "ok":published,"published":published,"count":job["count"],"path":job["path"],
            "partial_path":job["partial_path"],"errors":errors,"cleanup_error":cleanup_error}
        return -1
    finally:
        # 即使关闭或日志写入失败，旧任务也不能永久占用全局槽位。
        _JOB = None


def start(path, batch_size=200):
    global _JOB, _LAST_RESULT
    if _JOB is not None:
        raise RuntimeError("A job already exists; cancel it or wait for completion")
    _LAST_RESULT = None
    try:
        if not 1 <= batch_size <= 2000:
            raise ValueError("batch_size must be 1..2000")
        ready()
        meta = context()
        iterator = iter(module("idautils").Strings(False))
        path = os.path.abspath(os.fspath(path))
        if os.path.lexists(path):
            raise FileExistsError(path)
        partial_path = path+".partial"
        stream = open(partial_path,"x",encoding="utf-8")
    except Exception as exc:
        _LAST_RESULT = {"state":"failed","ok":False,"published":False,"path":str(path),"errors":[str(exc)]}
        raise
    job = {"stream":stream,"iterator":iterator,"count":0,"started":time.monotonic(),
           "cancel":False,"timer":None,"path":path,"partial_path":partial_path}
    _JOB = job
    _LAST_RESULT = None

    def tick():
        if _JOB is not job:
            return -1
        try:
            if job["cancel"]:
                return _finish(job,"cancelled")
            until = time.monotonic()+0.025
            for _ in range(batch_size):
                item = next(job["iterator"])
                record = {"ea":hex_ea(item.ea),"length":int(item.length),
                          "string_type":int(item.strtype),"text":str(item)}
                job["stream"].write(json.dumps(record,ensure_ascii=False)+"\n")
                job["count"] += 1
                if time.monotonic()>=until:
                    break
            job["stream"].flush()
        except StopIteration:
            return _finish(job,"complete")
        except Exception as exc:
            return _finish(job,"failed",str(exc))
        return 100

    try:
        stream.write(json.dumps({"event":"start","context":meta},ensure_ascii=False)+"\n")
        job["timer"] = module("ida_kernwin").register_timer(100,tick)
        if job["timer"] is None:
            raise RuntimeError("IDA could not register GUI timer")
    except Exception as exc:
        _finish(job,"failed",str(exc))
        raise RuntimeError("GUI export failed to start; inspect status() and partial file") from exc
    return "Started; cancel() requests termination. Check status().published and final file; .partial is not success."


def cancel():
    if _JOB is not None:
        _JOB["cancel"] = True
        return "Cancellation requested; next timer callback closes partial output"
    return "No active job"
