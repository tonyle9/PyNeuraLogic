from neuralogic.model import Atom, Model
from neuralogic.settings import Settings, Optimizer

settings = Settings(optimizer=Optimizer.SGD, epochs=300)


with Model().context() as model:
    # fmt: off

    # hidden<1-8> :- {1} a, {1} b.
    model.add_rules([Atom.get(f"hidden{i}") <= (Atom.a[1,], Atom.b[1,]) for i in range(1, 9)])

    # {1} xor :- hidden<1-8>.
    model.add_rules([Atom.xor[1,] <= Atom.get(f"hidden{i}") for i in range(1, 9)])

    model.add_examples(
        [  # Add 4 examples
            Atom.xor[0] <= (Atom.a[0], Atom.b[0]),
            Atom.xor[1] <= (Atom.a[1], Atom.b[0]),
            Atom.xor[1] <= (Atom.a[0], Atom.b[1]),
            Atom.xor[0] <= (Atom.a[1], Atom.b[1]),
        ]
    )
