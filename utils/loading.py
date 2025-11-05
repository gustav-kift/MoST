import time
import sys
import threading
import io
import contextlib
from colorama import Fore, Style, init

# Initialize Colorama
init()

CSI = "\x1b["  # ANSI Control Sequence Introducer

def _clear_current_stderr_line():
    # Move to start of line and erase the whole line (stderr)
    sys.stderr.write("\r" + CSI + "2K")
    sys.stderr.flush()

def animated_loading(wait_time=1.0, background_function=None, text="Loading",
                     finished_text="Worked for", interrupt_text="Stopped."):
    """
    Shows an animated loading effect on stderr while background_function runs.
    Captures the background_function's stdout and prints it AFTER the spinner stops.
    Final stdout will be exactly:
        Worked for <duration>
        <captured stdout from background>
    """
    gray = Style.DIM + Fore.WHITE   # Dull gray for all letters during the pause
    normal = Style.NORMAL + Fore.WHITE
    bright = Style.BRIGHT + Fore.WHITE
    reset = Style.RESET_ALL

    result = None
    output_buf = io.StringIO()

    def run_in_thread():
        nonlocal result
        if background_function:
            with contextlib.redirect_stdout(output_buf):
                result = background_function()

    try:
        start_time = time.time()

        background_thread = None
        if background_function:
            background_thread = threading.Thread(target=run_in_thread)
            background_thread.start()

        # Animate on STDERR until the background thread finishes
        while True:
            for i in range(len(text)):
                frame = ""
                for j in range(len(text)):
                    if j == i:
                        frame += f"{bright}{text[j]}{reset}"
                    elif j == i - 1 or j == i + 1:
                        frame += f"{normal}{text[j]}{reset}"
                    else:
                        frame += f"{gray}{text[j]}{reset}"
                sys.stderr.write(f"\r{frame}")
                sys.stderr.flush()
                time.sleep(0.1)

            sys.stderr.write(f"\r{gray}{text}{reset}")
            sys.stderr.flush()
            time.sleep(wait_time)

            if not background_thread or not background_thread.is_alive():
                break

        # Ensure worker is done
        if background_thread:
            background_thread.join()

        # Compute duration
        elapsed = int(time.time() - start_time)
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60

        if hours > 0:
            duration_text = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            duration_text = f"{minutes}m {seconds}s"
        else:
            duration_text = f"{seconds}s"

        # Clear the spinner line from STDERR
        _clear_current_stderr_line()

        # Print final lines to STDOUT only (clean)
        print(f"{gray}{finished_text} {duration_text}{reset}")

        captured = output_buf.getvalue()
        if captured:
            if not captured.endswith("\n"):
                captured += "\n"
            # Print exactly after "Worked for ..."
            sys.stdout.write(captured)
            sys.stdout.flush()

    except KeyboardInterrupt:
        _clear_current_stderr_line()
        print(interrupt_text)

    return result


# Example usage
if __name__ == "__main__":
    def example_background_task():
        time.sleep(5)
        print("hello world")

    animated_loading(wait_time=1.0,
                     background_function=example_background_task,
                     text="Thinking",
                     finished_text="Thought for")
