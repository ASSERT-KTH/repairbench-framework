import re
from decimal import Decimal


class ParseError(Exception):
    pass


class OutputParser:
    def __init__(self, output, strict=False):
        self.output = output
        self.lines = output.splitlines()
        self.strict = strict

    def parse(self):
        return [self.parse_line(line) for line in self.lines]

    def parse_line(self, line):
        elements = []
        tokens = re.finditer(r"\S+", line)
        for token in tokens:
            element = self.parse_element(token.group(0))
            if element is None:
                raise ParseError(f"Failed to match element at '{token.group(0)}'")
            elements.append(element)
        return elements

    def parse_element(self, token):
        if (number := self.parse_number(token)) is not None:
            return number
        return token

    def parse_number(self, token):
        if re.match(r"-?\d+(?:\.\d+)?$", token):
            return (
                int(token)
                if self.strict and re.match(r"^-?\d+$", token)
                else Decimal(token)
            )
        return None


DEFAULT_FLOAT_EPS = 1e-4
FLOAT_EPS = {
    "p02400": 1e-5,
    "p02008": 1e-6,
    "p03882": 1e-9,
    "p02805": 1e-6,
    "p03585": 1e-9,
    "p03619": 1e-11,
    "p01562": 1e-6,
    "p03428": 1e-5,
    "p01837": 1e-6,
    "p03135": 1e-3,
    "p02764": 1e-6,
    "p03888": 1e-6,
    "p03110": 1e-5,
    "p03901": 1e-6,
    "p01836": 1e-8,
    "p00973": 1e-6,
    "p03043": 1e-9,
    "p01948": 1e-6,
    "p01800": 1e-6,
    "p03304": 1e-6,
    "p01704": 1e-4,
    "p03001": 1e-9,
    "p02072": 1e-3,
    "p02897": 1e-6,
    "p03754": 1e-6,
    "p02731": 1e-6,
    "p03879": 1e-9,
    "p02677": 1e-9,
    "p03953": 1e-9,
    "p02894": 1e-9,
    "p02705": 1e-2,
    "p01825": 1e-6,
    "p03514": 1e-9,
    "p01672": 1e-8,
    "p02882": 1e-6,
    "p03881": 1e-9,
    "p02075": 1e-9,
    "p00988": 1e-7,
    "p03744": 1e-6,
    "p01685": 1e-6,
    "p03872": 1e-9,
    "p01703": 1e-8,
    "p03869": 1e-9,
    "p02884": 1e-6,
    "p03866": 1e-9,
    "p02780": 1e-6,
    "p01568": 1e-6,
    "p01705": 1e-4,
    "p01576": 1e-8,
    "p02935": 1e-5,
    "p03004": 1e-9,
    "p02011": 1e-6,
    "p01708": 1e-2,
    "p03776": 1e-6,
    "p02934": 1e-5,
    "p01363": 1e-6,
    "p01510": 1e-9,
    "p03871": 1e-9,
    "p02379": 1e-4,
}


def match(expected_output, actual_output, problem_id):
    if actual_output is None:
        return False

    expected_output = expected_output.rstrip("\n")
    actual_output = actual_output.rstrip("\n")
    if expected_output == actual_output:
        return True

    expected_parsed = OutputParser(expected_output).parse()
    actual_parsed = OutputParser(actual_output).parse()

    if len(expected_parsed) != len(actual_parsed):
        return False

    float_eps = FLOAT_EPS.get(problem_id, DEFAULT_FLOAT_EPS)

    for expected_line, actual_line in zip(expected_parsed, actual_parsed):
        if len(expected_line) != len(actual_line):
            return False

        for expected_element, actual_element in zip(expected_line, actual_line):
            if isinstance(expected_element, Decimal) and isinstance(
                actual_element, Decimal
            ):
                if abs(actual_element - expected_element) > float_eps:
                    return False
            elif actual_element != expected_element:
                return False

    return True
