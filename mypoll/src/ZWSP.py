"""
Zero Width Space module
"""

class ZWSP:
    """ Class to do work on zero width spaces """
    ZWSP_chars = ["\u200b", "\u200c", "\u200d", "\u200e", "\u200f",]
    numDigits = 4

    def __init__(self):
        self.maxNumber = len(self.ZWSP_chars)** self.numDigits - 1

    def getSequence(self, number):
        """ Given a number, return a string that is unique for that number"""
        assert  0 <= number <= self.maxNumber

        ret_string = ''
        for _ in range(self.numDigits):
            mod = number % len(self.ZWSP_chars)
            ret_string = self.ZWSP_chars[mod] + ret_string
            number = number // len(self.ZWSP_chars)
        return ret_string

    def getNumber(self, seq):
        """ Given a string, return an integer for that string"""
        assert len(seq) == self.numDigits

        ret_num = 0
        for i in range(self.numDigits):
            index = self.ZWSP_chars.index(seq[i])
            assert index >= 0
            ret_num = index + ret_num * len(self.ZWSP_chars)
        return ret_num

if __name__ == "__main__":
    import random
    # Test out ZWSP
    zwsp = ZWSP()
    assert zwsp.getSequence(0) == ''.join([zwsp.ZWSP_chars[0]*zwsp.numDigits])
    assert zwsp.getSequence(zwsp.maxNumber) == ''.join([zwsp.ZWSP_chars[-1]*zwsp.numDigits])
    num = int('0123', 5)
    assert zwsp.getSequence(num) == ''.join(zwsp.ZWSP_chars[0:4])

    num = random.randint(0, zwsp.maxNumber)
    seq1 = zwsp.getSequence(num)
    assert zwsp.getNumber(seq1) == num, f"number={num} seq=" + ''.join(list(seq1))
