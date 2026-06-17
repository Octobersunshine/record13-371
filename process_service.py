from flask import Flask, jsonify
import psutil

app = Flask(__name__)


def get_process_info(proc):
    try:
        with proc.oneshot():
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "cpu_percent": proc.cpu_percent(interval=0.1),
                "memory_mb": round(proc.memory_info().rss / (1024 * 1024), 2),
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


@app.route("/processes", methods=["GET"])
def get_processes():
    processes = []
    for proc in psutil.process_iter():
        info = get_process_info(proc)
        if info:
            processes.append(info)
    return jsonify({"processes": processes, "count": len(processes)})


@app.route("/processes/<int:pid>", methods=["GET"])
def get_process_by_pid(pid):
    try:
        proc = psutil.Process(pid)
        info = get_process_info(proc)
        if info:
            return jsonify(info)
    except psutil.NoSuchProcess:
        return jsonify({"error": f"Process with PID {pid} not found"}), 404
    except psutil.AccessDenied:
        return jsonify({"error": f"Access denied to process with PID {pid}"}), 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
