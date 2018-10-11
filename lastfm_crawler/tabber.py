"""A simple table generator for visualizing progress during execution"""

import sys
import time


class Tabber:
    _start_width = 12

    def __init__(self, *args, width=_start_width, auto=True, time_execution=True):
        """
        Creates new Tabber object and optionally outputs a header

        :param args: Optional header elements
        :param width: Overrides default minimum width of columns. Default is 12
        :param auto: Should column width be extended if header items are longer than column width. Default: True
        :param time: Should an addition column be added to display time since creation of tabber. Default: True
        """
        self.width = width
        self.time_execution = time_execution
        self._creation_time = time.time()
        if len(args) > 0:
            self.write_header(*args, auto=auto)

    def __call__(self, *args):
        """
        Update the latest table line. Potentially overwrites previously printed data

        :param args: Items to output
        """
        self.write(*args)

    def write(self, *args, auto=False, add_time=True):
        """
        Update the latest table line. Potentially overwrites previously printed data

        tab.write(1, 1337, 42) outputs:

        |            1 |         1337 |           42 |

        with the default with of 12

        :param args: Items to output
        :param auto: Should column width be extended if header items are longer than column width. Default: False
        :param add_time: Should the current elapsed time be added to the line if execution timing is enabled.
        """
        if self.time_execution and add_time:
            sys.stdout.write(self._str_fmt(*args,
                                           time.strftime("%H:%M:%S", time.gmtime(time.time() - self._creation_time)),
                                           auto=auto))
        else:
            sys.stdout.write(self._str_fmt(*args, auto=auto))
        sys.stdout.write("\r")

    def write_line(self, *args, auto=False, add_time=True):
        """
        Update the latest table line. Potentially overwrites previously printed data

        tab.write(1, 1337, 42) outputs:

        |            1 |         1337 |          42 |

        with the default width of 12

        :param args: Items to output
        :param auto: Should column width be extended if header items are longer than column width. Default: False
        :param add_time: Should the current elapsed time be added to the line if execution timing is enabled.
        """
        self.write(*args, auto=auto, add_time=add_time)
        sys.stdout.write("\n")

    def _spacer(self, c):
        return "|{}|".format("+".join(["-" * (self.width + 2) for _ in range(c)]))

    def write_header(self, *args, auto=True):
        """
        Outputs the header for a new table by outputting a line feed, a row with header
        items and a spacer

        tab.write_header("read", "skipped", written") outputs:
        \\n
        |         read |      skipped |      written |
        |--------------+--------------+--------------+\\n

        with the default width of 12

        :param args: Header elements
        :param auto: Should column width be extended if header items are longer than column width. Default: True
        """
        print("")
        if self.time_execution:
            self.write_line(*args, "time", auto=auto, add_time=False)
            print(self._spacer(len(args) + 1))
        else:
            self.write_line(*args, auto=auto)
            print(self._spacer(len(args)))

    def _str_fmt(self, *args, auto=False):
        if auto:
            strs = [str(s) for s in args]
            self.width = max(self.width, max(map(lambda x: len(x), strs)))
            return self._str_fmt(*strs)
        return "| {} |".format(" | ".join(map(lambda x: str(x).rjust(self.width), args)))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("")


if __name__ == "__main__":
    with Tabber("total", "div 256", "evens") as tab:
        dv_256 = 0
        evens = 0
        i = 0
        while i < 10000000:
            if i & 1 == 0:
                evens += 1
            if i & 255 == 0:
                dv_256 += 1
                tab(i, dv_256, evens)
            i += 1
        tab(i, dv_256, evens)
