import sys


def select_option_interactive(options,index=False):
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
        if index:
            return answer
        return options[answer]

