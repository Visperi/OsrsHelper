"""
MIT License

Copyright (c) 2018 Visperi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

modulelist = ["bs4", "discord", "tabulate"]


def check_modules():
    """
    Function to check if all necessary modules are installed in the bot hosting computer.
    """

    import sys

    not_found = 0
    version_info = sys.version_info
    version_minor = "{}.{}".format(version_info[0], version_info[1])
    message = "OK"

    if float(version_minor) < 3.6:
        message = "PLEASE UPDATE TO VERSION 3.6+"
    print("Python version: {}.{}.{}     {}\n".format(version_info[0], version_info[1], version_info[2], message))
    for module in modulelist:
        try:
            __import__(module)
            dots = "." * (35 - len(module) + 2)
            print("{}{}OK".format(module, dots))
        except ModuleNotFoundError:
            not_found += 1
            dots = "." * (35 - (len(module) + 5))
            print("{}{}NOT FOUND".format(module, dots))
    print("")
    if not_found > 0:
        print("Modules not found must be installed for the bot to work. Program will exit now.")
    else:
        print("All necessary modules are installed. Program will exit now.")
    input("Press enter to continue.")
    exit()


if __name__ == '__main__':
    check_modules()
