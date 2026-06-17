import logging
from flask import Flask, jsonify
import psutil

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_process_info(proc):
    try:
        with proc.oneshot():
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "cpu_percent": proc.cpu_percent(interval=0.1),
                "memory_mb": round(proc.memory_info().rss / (1024 * 1024), 2),
            }
    except psutil.NoSuchProcess:
        logger.warning("Process PID %s no longer exists, skipping", proc.pid)
    except psutil.AccessDenied:
        logger.warning("Access denied to process PID %s, skipping", proc.pid)
    except Exception as e:
        logger.error("Failed to get info for process PID %s: %s", proc.pid, e)
    return None


@app.route("/processes", methods=["GET"])
def get_processes():
    processes = []
    skipped = 0
    for proc in psutil.process_iter():
        info = get_process_info(proc)
        if info:
            processes.append(info)
        else:
            skipped += 1
    logger.info("Retrieved %d processes, skipped %d", len(processes), skipped)
    return jsonify({
        "processes": processes,
        "count": len(processes),
        "skipped": skipped,
    })


@app.route("/processes/<int:pid>", methods=["GET"])
def get_process_by_pid(pid):
    try:
        proc = psutil.Process(pid)
        info = get_process_info(proc)
        if info:
            return jsonify(info)
        return jsonify({"error": f"Failed to retrieve info for process with PID {pid}"}), 500
    except psutil.NoSuchProcess:
        logger.warning("Process PID %d not found", pid)
        return jsonify({"error": f"Process with PID {pid} not found"}), 404
    except psutil.AccessDenied:
        logger.warning("Access denied to process PID %d", pid)
        return jsonify({"error": f"Access denied to process with PID {pid}"}), 403
    except Exception as e:
        logger.error("Unexpected error for process PID %d: %s", pid, e)
        return jsonify({"error": f"Internal server error: {e}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
