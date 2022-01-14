import sys

"""
Functionalities for user interaction.
"""

def select_option_interactive(options,pos=False):
    """
    Tool to allow user to select on of the options passed to the function.
    
    Parameters:
        options (list):  List of strings or objects (works as long as str(object) works)
        pos (bool): If only the position of the answer is of interest.  Optional, default is False.
    
    Returns:
        Option (so string or object) selected by the user. 
        If pos=True, then only the index of the selected option is returned.

    """

    print(f"\n Please select one of the following options!")
    for index, option in zip(range(0,len(options)),options):
        print(f"[{index + 1}]: {option}")
    answer_accepted = False
    answer = 0
    while not answer_accepted:       
        answer = sys.stdin.readline()[:-1]
        try:
            answer = int(answer) - 1
            if len(options) > answer >= 0:
                answer_accepted = True
            else:
                print(f"{answer + 1} is not in range of"
                                  f"[{1},{len(options)}],"
                                  f"please select again!")
        except ValueError:
            print(f"{answer} is not a number,"
                              f"please select again!")
        if pos:
            return answer
        return options[answer]

