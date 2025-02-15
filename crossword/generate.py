import sys
from collections import deque
from crossword import *
from crossword import Variable, Crossword


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for variable, words in self.domains.items():
            words_to_remove = set()
            for word in words:
                if len(word)!= variable.length:
                    words_to_remove.add(word)
            self.domains[variable] = words.difference(words_to_remove)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised =  False
        overlap = self.crossword.overlaps[x,y]

        if overlap:
            v1, v2 = overlap
            xs_to_remove = set()
            for x_i in self.domains[x]:
                overlaps = False
                for y_j in self.domains[y]:
                    if x_i != y_j and x_i[v1]==y_j[v2]:
                        overlaps = True
                        break
                if not overlaps:
                    xs_to_remove.add(x_i)
            if xs_to_remove:
                self.domains[x] = self.domains[x].difference(xs_to_remove)
                revised = True
        return revised




    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs is  None:
            arcs = deque()
            for v1 in self.crossword.variables:
                for v2 in self.crossword.neighbors(v1):
                    arcs.appendleft((v1,v2))
            else:
                arcs = deque(arcs)
            while arcs:
                x,y = arcs.pop()
                if self.revise(x,y):
                    if len(self.domains[x]) == 0:
                        return False
                    for z in self.crossword.neighbors(x)- {y}:
                        arcs.appendleft((z,x))
            return True


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for variable in self.crossword.variables:
            if variable not in assignment.keys():
                return False
            if assignment[variable] not in self.crossword.words:
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        for variable_x,word_x in assignment.items():
            if variable_x.length != len(word_x):
                return False

            for variable_y, word_y in assignment.items():
                if variable_x != variable_y:
                    if word_x == word_y:
                        return False

                    overlap = self.crossword.overlaps[variable_x, variable_y]
                    if overlap:
                        a, b = overlap
                        if word_x[a]!= word_y[b]:
                            return False
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        neighbors = self.crossword.neighbors(var)
        for variable in assignment:
            if variable in neighbors:
                neighbors.remove(variable)

        result = []
        for variable in self.domains[var]:
            ruled_out = 0
            for neighbor in neighbors:
                for variable_2 in self.domains[neighbor]:
                    overlap = self.crossword.overlaps[var,neighbor]
                    if overlap:
                        a, b = overlap
                        if variable[a]!= variable_2[b]:
                            ruled_out += 1
            result.append([variable, ruled_out])
        result.sort(key=lambda x:x[1])
        return[i[0] for i in result]

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        potential_variables = []
        for variable in self.crossword.variables:
                if variable not in assignment:
                   potential_variables.append([variable, len(self.domains[variable]),len(self.crossword.neighbors(variable))])

        if potential_variables:
                potential_variables.sort(key=lambda x:(x[1], -x[2]))
                return potential_variables[0][0]

        return None


    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment): return assignment
        variable = self.select_unassigned_variable(assignment)

        for value in self.order_domain_values(variable,assignment):
            assignment[variable]=value
            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result:
                    return result
                assignment.pop(variable,None)
        return None

def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()